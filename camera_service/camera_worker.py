from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import cv2

from event_sender import EventSender
from face_recognition import FaceRecognitionAdapter
from object_detection import Detection, YoloObjectDetector


class EventDebouncer:
    def __init__(self, cooldown_sec: float):
        self.cooldown_sec = cooldown_sec
        self.last_sent: dict[tuple, float] = {}

    def allow(self, key: tuple) -> bool:
        now = time.monotonic()
        previous = self.last_sent.get(key, 0)
        if now - previous < self.cooldown_sec:
            return False
        self.last_sent[key] = now
        return True


class ClassroomBehaviorTracker:
    def __init__(self, expected_students: int = 4):
        self.expected_students = expected_students
        self.tracks: dict[str, dict] = {}
        self.next_id = 1

    def update(self, detections: list[dict], frame_width: int, frame_height: int, video_time_sec: float) -> tuple[list[dict], list[dict]]:
        teacher = next((item for item in detections if item.get("role") == "teacher"), None)
        students = [item for item in detections if item.get("role") == "student"]
        assigned: set[str] = set()

        for student in students:
            track_id = self._match_track(student, assigned)
            if not track_id:
                track_id = f"student-{self.next_id:02d}"
                self.next_id += 1
                self.tracks[track_id] = {
                    "name": student.get("name") or f"Ученик {self.next_id - 1:02d}",
                    "box": student["box"],
                    "last_seen": video_time_sec,
                    "missing_since": None,
                    "last_near_exit": False,
                    "exit_reported": False,
                    "attention": 78,
                }

            attention = estimate_student_attention(student, teacher, frame_width, frame_height)
            track = self.tracks[track_id]
            track.update(
                {
                    "name": student.get("name") or track["name"],
                    "box": student["box"],
                    "last_seen": video_time_sec,
                    "missing_since": None,
                    "last_near_exit": is_near_exit_zone(student["box"], frame_width, frame_height),
                    "exit_reported": False if not track.get("exit_reported") else track["exit_reported"],
                    "attention": attention,
                }
            )
            student["track_id"] = track_id
            student["attention"] = attention
            student["status"] = "visible"
            assigned.add(track_id)

        events = []
        for track_id, track in list(self.tracks.items()):
            if track_id in assigned:
                continue
            if video_time_sec - track.get("last_seen", 0) > 30:
                self.tracks.pop(track_id, None)
                continue

            if track.get("missing_since") is None:
                track["missing_since"] = video_time_sec

            occluded = is_occluded_by_teacher(track["box"], teacher)
            missing_for = video_time_sec - track["missing_since"]
            if occluded:
                events.append(
                    {
                        "type": "student_occluded",
                        "level": "info",
                        "title": f"{track['name']} временно закрыт учителем",
                        "text": "Не считаем выходом из класса: ученик был перекрыт рамкой учителя.",
                        "student": track["name"],
                    }
                )
                continue

            if track.get("last_near_exit") and missing_for >= 4.0 and not track.get("exit_reported"):
                track["exit_reported"] = True
                events.append(
                    {
                        "type": "student_left_classroom",
                        "level": "warning",
                        "title": f"{track['name']} мог выйти из кабинета",
                        "text": "Ученик исчез после появления рядом с дверной зоной. Требуется подтверждение учителем.",
                        "student": track["name"],
                    }
                )

        attention_rows = [
            {
                "student": track["name"],
                "attention": track.get("attention"),
                "status": "visible" if track_id in assigned else ("occluded_by_teacher" if is_occluded_by_teacher(track["box"], teacher) else "not_visible"),
                "last_seen": round(track.get("last_seen", 0), 2),
            }
            for track_id, track in sorted(self.tracks.items())
        ][: self.expected_students]
        return attention_rows, events

    def _match_track(self, student: dict, assigned: set[str]) -> str | None:
        center = box_center_xywh(student["box"])
        best_id = None
        best_distance = 999999.0
        for track_id, track in self.tracks.items():
            if track_id in assigned:
                continue
            distance = point_distance(center, box_center_xywh(track["box"]))
            if distance < best_distance:
                best_distance = distance
                best_id = track_id
        return best_id if best_distance < 260 else None


def parse_args():
    parser = argparse.ArgumentParser(description="EduCam camera recognition worker")
    parser.add_argument("--backend", default="http://127.0.0.1:5000")
    parser.add_argument("--lesson-id", type=int, required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--source", default="0", help="Webcam index, video file, RTSP URL, or HTTP stream")
    parser.add_argument("--source-config", default="", help="JSON file with source_type and source fields")
    parser.add_argument("--camera-name", default="camera-1")
    parser.add_argument("--room", default="")
    parser.add_argument("--lesson-title", default="")
    parser.add_argument("--teacher-name", default="")
    parser.add_argument("--student-count", type=int, default=0)
    parser.add_argument("--disable-phone-candidates", action="store_true")
    parser.add_argument(
        "--enable-phone-candidates",
        action="store_true",
        help="Allow heuristic OpenCV phone candidates when YOLO does not find phones.",
    )
    parser.add_argument("--model", default="yolov8n.pt", help="YOLO model path, for example yolov8n.pt")
    parser.add_argument("--imgsz", type=int, default=960, help="YOLO inference size. Lower is faster.")
    parser.add_argument("--faces-dir", default="", help="Folder with known faces: faces_db/<student name>/*.jpg")
    parser.add_argument("--state-file", default="", help="JSON file consumed by the EduCam camera page")
    parser.add_argument("--snapshot-file", default="", help="JPEG frame consumed by the EduCam camera page")
    parser.add_argument("--face-threshold", type=float, default=78.0)
    parser.add_argument("--confidence", type=float, default=0.35)
    parser.add_argument("--every-n-frames", type=int, default=5)
    parser.add_argument("--cooldown-sec", type=float, default=20.0)
    parser.add_argument("--realtime", action="store_true", help="Throttle file playback to camera-like realtime")
    parser.add_argument("--display", action="store_true", help="Show local OpenCV preview window")
    parser.add_argument("--dry-run", action="store_true", help="Print events instead of sending them")
    return parser.parse_args()


def open_source(source: str):
    if source.isdigit():
        return cv2.VideoCapture(int(source))
    return cv2.VideoCapture(source)


def read_source_config(config_path: str, fallback_source: str) -> str:
    if not config_path:
        return fallback_source
    path = Path(config_path)
    if not path.exists():
        return fallback_source
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback_source
    return data.get("source") or fallback_source


def main():
    args = parse_args()
    detector = YoloObjectDetector(args.model, confidence=args.confidence, imgsz=args.imgsz)
    recognizer = None
    if args.faces_dir:
        recognizer = FaceRecognitionAdapter(Path(args.faces_dir), threshold=args.face_threshold)

    sender = EventSender(args.backend, args.token)
    debouncer = EventDebouncer(args.cooldown_sec)
    behavior_tracker = ClassroomBehaviorTracker(args.student_count or 4)
    current_source = read_source_config(args.source_config, args.source)
    capture = open_source(current_source)
    next_config_check = time.monotonic() + 2
    config_mtime = Path(args.source_config).stat().st_mtime if args.source_config and Path(args.source_config).exists() else 0

    if not capture.isOpened():
        raise RuntimeError(f"Cannot open camera source: {current_source}")

    frame_index = 0
    fps = capture.get(cv2.CAP_PROP_FPS) or 25
    print(f"EduCam worker started: source={current_source}, lesson_id={args.lesson_id}, camera={args.camera_name}")

    while True:
        if args.source_config and time.monotonic() >= next_config_check:
            next_config_check = time.monotonic() + 2
            path = Path(args.source_config)
            mtime = path.stat().st_mtime if path.exists() else 0
            if mtime != config_mtime:
                next_source = read_source_config(args.source_config, current_source)
                config_mtime = mtime
                if next_source != current_source:
                    print(f"switching camera source: {next_source}")
                    capture.release()
                    current_source = next_source
                    capture = open_source(current_source)
                    frame_index = 0
                    fps = capture.get(cv2.CAP_PROP_FPS) or 25

        ok, frame = capture.read()
        if not ok:
            if not current_source.isdigit() and Path(current_source).exists():
                capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                continue
            time.sleep(0.5)
            continue

        frame_index += 1
        video_time_sec = (capture.get(cv2.CAP_PROP_POS_MSEC) or 0) / 1000
        if frame_index % max(args.every_n_frames, 1) != 0:
            if args.display:
                cv2.imshow("EduCam camera worker", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
            if args.realtime:
                time.sleep(1 / max(fps, 1))
            continue

        detections = detector.detect(frame)
        faces = recognizer.recognize(frame) if recognizer else []
        known_names = [face.name for face in faces if face.name]
        people = [item for item in detections if item.label == "person"]
        phones = [item for item in detections if item.label == "cell phone"]
        if args.disable_phone_candidates:
            detections = [item for item in detections if item.label != "cell phone"]
            phones = []
        if not phones and args.enable_phone_candidates and not args.disable_phone_candidates:
            candidates = detect_phone_candidates(frame, people)
            detections.extend(candidates)
            phones = candidates
        attention = estimate_attention(len(people), len(faces), len(phones))

        if args.state_file:
            write_state(
                Path(args.state_file),
                args,
                frame,
                detections,
                faces,
                attention,
                video_time_sec,
                behavior_tracker,
            )
        if args.snapshot_file:
            write_snapshot(Path(args.snapshot_file), frame)

        for name in known_names:
            maybe_send(
                args,
                sender,
                debouncer,
                event_type="student_arrived",
                student_name=name,
                key=("student_arrived", name),
                payload={"camera": args.camera_name, "recognition": "face_lbph"},
            )

        if people and not known_names:
            maybe_send(
                args,
                sender,
                debouncer,
                event_type="student_arrived",
                student_name=None,
                key=("person_detected", args.camera_name),
                payload={
                    "camera": args.camera_name,
                    "people_count": len(people),
                    "detections": [asdict(item) for item in people[:10]],
                },
            )

        if phones:
            maybe_send(
                args,
                sender,
                debouncer,
                event_type="distraction_detected",
                student_name=known_names[0] if known_names else None,
                key=("phone_detected", known_names[0] if known_names else args.camera_name),
                payload={
                    "camera": args.camera_name,
                    "reason": "cell_phone_detected",
                    "phones_count": len(phones),
                    "detections": [asdict(item) for item in phones[:10]],
                },
            )

        if args.display:
            draw_overlay(frame, detections, faces)
            cv2.imshow("EduCam camera worker", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        elif args.realtime:
            time.sleep(0)

    capture.release()
    cv2.destroyAllWindows()


def maybe_send(args, sender, debouncer, event_type, student_name, key, payload):
    if not debouncer.allow(key):
        return

    event = {
        "lesson_id": args.lesson_id,
        "event_type": event_type,
        "student_name": student_name,
        "payload": payload,
    }

    if args.dry_run:
        print(json.dumps(event, ensure_ascii=False))
        return

    try:
        result = sender.send(**event)
        print(f"sent {event_type}: {result}")
    except Exception as exc:
        print(f"event send skipped ({event_type}): {exc}")


def write_snapshot(snapshot_path: Path, frame) -> None:
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = snapshot_path.with_name(f"{snapshot_path.stem}.{os.getpid()}.jpg")
    cv2.imwrite(str(temp_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
    for attempt in range(8):
        try:
            temp_path.replace(snapshot_path)
            break
        except PermissionError:
            if attempt == 7:
                print(f"snapshot write skipped: {snapshot_path} is locked")
                break
            time.sleep(0.04)
    if temp_path.exists():
        try:
            temp_path.unlink()
        except PermissionError:
            pass


def estimate_attention(people_count: int, faces_count: int, phones_count: int) -> int:
    if people_count <= 0 and faces_count <= 0:
        return 0

    visible_people = max(people_count, faces_count, 1)
    face_ratio = min(faces_count / visible_people, 1.0)
    phone_penalty = min(phones_count * 12, 38)
    attention = 72 + int(face_ratio * 18) - phone_penalty
    return max(20, min(attention, 98))


def normalize_detection(detection):
    x1, y1, x2, y2 = detection.box
    return [int(x1), int(y1), int(max(1, x2 - x1)), int(max(1, y2 - y1))]


def detect_phone_candidates(frame, people: list[Detection], limit: int = 3) -> list[Detection]:
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    _, mask = cv2.threshold(blurred, 65, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    height, width = frame.shape[:2]
    people_boxes = [person.box for person in people]
    candidates: list[tuple[float, Detection]] = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < 450 or area > 8500:
            continue
        if y < height * 0.28 or y > height * 0.9:
            continue
        aspect = w / max(h, 1)
        if aspect < 0.45 or aspect > 3.2:
            continue
        if any(overlap_ratio((x, y, x + w, y + h), box) > 0.2 for box in people_boxes):
            continue

        rectangularity = cv2.contourArea(contour) / max(area, 1)
        if rectangularity < 0.35:
            continue
        center_bonus = 1.0 - min(abs((x + w / 2) - width * 0.58) / width, 0.35)
        score = min(0.62, 0.28 + rectangularity * 0.22 + center_bonus * 0.12)
        candidates.append((score, Detection("cell phone", float(score), (x, y, x + w, y + h))))

    candidates.sort(key=lambda item: item[0], reverse=True)
    return [candidate for _, candidate in candidates[:limit]]


def overlap_ratio(box_a, box_b) -> float:
    ax1, ay1, ax2, ay2 = box_a
    bx1, by1, bx2, by2 = box_b
    x1 = max(ax1, bx1)
    y1 = max(ay1, by1)
    x2 = min(ax2, bx2)
    y2 = min(ay2, by2)
    if x2 <= x1 or y2 <= y1:
        return 0.0
    intersection = (x2 - x1) * (y2 - y1)
    area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
    return intersection / area_a


def box_center_xywh(box: list[int] | tuple[int, int, int, int]) -> tuple[float, float]:
    x, y, w, h = box
    return x + w / 2, y + h / 2


def point_distance(point_a: tuple[float, float], point_b: tuple[float, float]) -> float:
    return ((point_a[0] - point_b[0]) ** 2 + (point_a[1] - point_b[1]) ** 2) ** 0.5


def xywh_to_xyxy(box: list[int] | tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    x, y, w, h = box
    return int(x), int(y), int(x + w), int(y + h)


def is_occluded_by_teacher(student_box: list[int], teacher: dict | None) -> bool:
    if not teacher or not teacher.get("box"):
        return False
    teacher_box = xywh_to_xyxy(teacher["box"])
    student_xyxy = xywh_to_xyxy(student_box)
    if overlap_ratio(student_xyxy, teacher_box) > 0.18:
        return True
    sx, sy = box_center_xywh(student_box)
    tx, ty = box_center_xywh(teacher["box"])
    return abs(sx - tx) < 170 and abs(sy - ty) < 260


def is_near_exit_zone(box: list[int], frame_width: int, frame_height: int) -> bool:
    center_x, center_y = box_center_xywh(box)
    return frame_width * 0.24 <= center_x <= frame_width * 0.43 and center_y <= frame_height * 0.62


def estimate_student_attention(student: dict, teacher: dict | None, frame_width: int, frame_height: int) -> int:
    confidence = float(student.get("confidence", 0.4))
    x, y, w, h = student["box"]
    center_y = y + h / 2
    seated_bonus = 8 if center_y > frame_height * 0.42 else -4
    size_bonus = min((w * h) / max(frame_width * frame_height, 1) * 180, 12)
    occlusion_penalty = 16 if is_occluded_by_teacher(student["box"], teacher) else 0
    attention = 62 + confidence * 22 + seated_bonus + size_bonus - occlusion_penalty
    return int(max(35, min(96, attention)))


def face_confidence_score(raw_confidence: float, threshold: float) -> float:
    if raw_confidence >= 900:
        return 0.0
    score = 1.0 - min(raw_confidence / max(threshold, 1.0), 1.0)
    return round(max(0.0, score), 3)


def write_state(
    state_path: Path,
    args,
    frame,
    detections,
    faces,
    attention: int,
    video_time_sec: float = 0,
    behavior_tracker: ClassroomBehaviorTracker | None = None,
):
    height, width = frame.shape[:2]
    state_path.parent.mkdir(parents=True, exist_ok=True)
    items = []
    recognitions = []
    people = suppress_overlapping_people([item for item in detections if item.label == "person"])
    teacher_override = detect_teacher_by_white_clothes(frame)
    teacher_box = teacher_override.box if teacher_override else choose_teacher_box(
        frame,
        people,
        teacher_name=args.teacher_name,
    )
    raw_teacher_box = teacher_box
    refined_teacher_box = refine_teacher_box(frame, teacher_box) if teacher_box else None
    if refined_teacher_box and teacher_override:
        teacher_override = Detection("person", teacher_override.confidence, refined_teacher_box)
    teacher_box = refined_teacher_box or raw_teacher_box
    student_boxes = choose_student_boxes(
        [item for item in detections if item.label == "person"],
        raw_teacher_box,
        limit=args.student_count or 4,
    )
    student_index = 1

    if teacher_override:
        teacher_item = {
            "label": "person",
            "role": "teacher",
            "name": args.teacher_name or "Учитель",
            "confidence": round(float(teacher_override.confidence), 3),
            "box": normalize_detection(teacher_override),
            "detail": "OpenCV white-clothes teacher tracking",
        }
        items.append(teacher_item)
        recognitions.append(teacher_item)

    for detection in detections:
        if teacher_override and detection.label == "person" and overlap_ratio(detection.box, teacher_box) > 0.25:
            continue
        if detection.label == "person" and not teacher_override and detection.box != raw_teacher_box and detection.box not in student_boxes:
            continue
        if detection.label == "person" and teacher_override and detection.box not in student_boxes:
            continue
        role = "phone" if detection.label == "cell phone" else "student"
        display_name = None
        if detection.label == "person" and raw_teacher_box and detection.box == raw_teacher_box:
            role = "teacher"
            display_name = args.teacher_name or "Учитель"
        elif detection.label == "person":
            display_name = f"Не распознанный человек {student_index:02d}"
            student_index += 1

        item = {
            "label": detection.label,
            "role": role,
            "name": display_name,
            "confidence": round(float(detection.confidence), 3),
            "box": normalize_detection(Detection(detection.label, detection.confidence, teacher_box)) if role == "teacher" and teacher_box else normalize_detection(detection),
            "detail": teacher_detail(role) if role == "teacher" else ("OpenCV phone candidate" if role == "phone" and detection.confidence < 0.7 else "YOLO object detection"),
        }
        items.append(item)
        if detection.label == "cell phone" or role == "teacher":
            recognitions.append(item)

    for index, face in enumerate(faces, start=1):
        if not face.name:
            continue
        name = face.name or f"Ученик {index:02d}"
        role = "teacher" if args.teacher_name and face.name == args.teacher_name else "student"
        score = face_confidence_score(face.confidence, args.face_threshold)
        item = {
            "label": "face",
            "role": role,
            "name": name,
            "confidence": score,
            "box": [int(value) for value in face.box],
            "detail": "OpenCV LBPH face recognition" if face.name else "OpenCV face detected",
        }
        items.append(item)
        recognitions.append(item)

    student_attention, behavior_events = ([], [])
    if behavior_tracker:
        student_attention, behavior_events = behavior_tracker.update(items, width, height, video_time_sec)

    visible_people = [item for item in items if item["label"] == "person"]
    visible_phones = [item for item in items if item["label"] == "cell phone"]
    if visible_phones:
        behavior_events = [
            {
                "type": "phone_detected",
                "level": "warning",
                "title": "Телефон в кадре",
                "text": "AI обнаружил телефон на реальной камере или демо-видео.",
            },
            *behavior_events,
        ]
    visible_students = [item for item in items if item.get("role") == "student"]
    visible_attention = [item.get("attention") for item in visible_students if item.get("attention") is not None]
    if visible_attention:
        attention = int(sum(visible_attention) / len(visible_attention))
    state = {
        "camera": args.camera_name,
        "room": args.room,
        "lesson": args.lesson_title,
        "teacher": args.teacher_name,
        "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "video_time_sec": round(float(video_time_sec), 2),
        "attention": attention,
        "people_count": len(visible_people),
        "phones_count": len(visible_phones),
        "frame_width": width,
        "frame_height": height,
        "detections": items,
        "recognitions": recognitions,
        "student_attention": student_attention,
        "events": behavior_events,
    }

    temp_path = state_path.with_name(f"{state_path.stem}.{os.getpid()}.tmp")
    with temp_path.open("w", encoding="utf-8") as state_file:
        json.dump(state, state_file, ensure_ascii=False, indent=2)
    for attempt in range(8):
        try:
            temp_path.replace(state_path)
            break
        except PermissionError:
            if attempt == 7:
                print(f"state write skipped: {state_path} is locked")
                break
            time.sleep(0.04)
    if temp_path.exists():
        try:
            temp_path.unlink()
        except PermissionError:
            pass


def suppress_overlapping_people(people: list[Detection]) -> list[Detection]:
    people = sorted(people, key=lambda item: item.confidence, reverse=True)
    kept: list[Detection] = []
    for detection in people:
        if all(
            max(overlap_ratio(detection.box, item.box), overlap_ratio(item.box, detection.box)) < 0.45
            for item in kept
        ):
            kept.append(detection)
    return kept


def detect_teacher_by_white_clothes(frame) -> Detection | None:
    height, width = frame.shape[:2]
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, (0, 0, 138), (180, 105, 255))

    roi_mask = mask.copy()
    roi_mask[: int(height * 0.24), :] = 0
    roi_mask[int(height * 0.92) :, :] = 0
    roi_mask[:, : int(width * 0.18)] = 0
    roi_mask[:, int(width * 0.9) :] = 0

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    roi_mask = cv2.morphologyEx(roi_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    roi_mask = cv2.dilate(roi_mask, kernel, iterations=1)
    contours, _ = cv2.findContours(roi_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    candidates: list[tuple[float, Detection]] = []

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < 2600 or area > 85000:
            continue
        if w > 360 or h > 360:
            continue
        if h < 42 or w < 42:
            continue
        aspect = h / max(w, 1)
        if aspect < 0.35 or aspect > 2.8:
            continue

        contour_area = cv2.contourArea(contour)
        fill_ratio = contour_area / max(area, 1)
        center_x = x + w / 2
        center_y = y + h / 2
        if center_y < height * 0.32 or center_y > height * 0.78:
            continue

        # Build a person-sized box from the visible light blouse. The teacher
        # may be bent over a student, so extend more downward than upward.
        person_x1 = int(max(0, x - w * 0.35))
        person_y1 = int(max(0, y - h * 0.45))
        person_x2 = int(min(width, x + w * 1.35))
        person_y2 = int(min(height, y + h * 2.95))
        person_h = person_y2 - person_y1
        person_w = person_x2 - person_x1
        if person_h < 190 or person_w < 90:
            continue

        desk_zone_bonus = 55 if center_x > width * 0.5 else 20
        blouse_score = min(fill_ratio, 1.0) * 210 + min(area / 18000, 1.0) * 100
        score = blouse_score + desk_zone_bonus + min(center_y / height, 1.0) * 35
        confidence = max(0.58, min(0.92, score / 360))
        candidates.append((score, Detection("person", confidence, (person_x1, person_y1, person_x2, person_y2))))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1]


def refine_teacher_box(frame, box: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
    height, width = frame.shape[:2]
    x1, y1, x2, y2 = box
    box_w = max(1, x2 - x1)
    box_h = max(1, y2 - y1)

    expanded_x1 = int(max(0, x1 - box_w * 0.16))
    expanded_y1 = int(max(0, y1 - box_h * 0.18))
    expanded_x2 = int(min(width, x2 + box_w * 0.12))
    expanded_y2 = int(min(height, y2 + box_h * 0.05))

    roi = frame[expanded_y1:expanded_y2, expanded_x1:expanded_x2]
    if roi.size:
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        white_mask = cv2.inRange(hsv, (0, 0, 125), (180, 120, 255))
        contours, _ = cv2.findContours(white_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        white_boxes = []
        for contour in contours:
            wx, wy, ww, wh = cv2.boundingRect(contour)
            if ww * wh < 220:
                continue
            white_boxes.append((expanded_x1 + wx, expanded_y1 + wy, expanded_x1 + wx + ww, expanded_y1 + wy + wh))
        if white_boxes:
            min_x = min(item[0] for item in white_boxes)
            min_y = min(item[1] for item in white_boxes)
            max_x = max(item[2] for item in white_boxes)
            expanded_x1 = int(max(0, min(expanded_x1, min_x - box_w * 0.12)))
            expanded_y1 = int(max(0, min(expanded_y1, min_y - box_h * 0.18)))
            expanded_x2 = int(min(width, max(expanded_x2, max_x + box_w * 0.12)))

    return expanded_x1, expanded_y1, expanded_x2, expanded_y2


def teacher_detail(role: str) -> str:
    if role == "teacher":
        return "YOLO + white-clothes teacher selection"
    return "YOLO object detection"


def choose_student_boxes(people: list[Detection], teacher_box, limit: int = 4) -> set[tuple[int, int, int, int]]:
    candidates = []
    for detection in suppress_overlapping_people(people):
        if teacher_box and (
            detection.box == teacher_box
            or overlap_ratio(detection.box, teacher_box) > 0.18
            or overlap_ratio(teacher_box, detection.box) > 0.18
        ):
            continue
        x1, y1, x2, y2 = detection.box
        area = max(1, (x2 - x1) * (y2 - y1))
        # Students in this demo are seated at desks, so favor lower-center
        # and desk-side detections after the moving teacher is removed.
        center_y = (y1 + y2) / 2
        center_x = (x1 + x2) / 2
        seated_bonus = 1.15 if center_y > 430 else 0.85
        desk_side_bonus = 1.12 if center_x < 760 or center_x > 1020 else 1.0
        candidates.append((detection.confidence * area * seated_bonus * desk_side_bonus, detection.box))
    candidates.sort(reverse=True)
    return {box for _, box in candidates[:limit]}


def choose_teacher_box(frame, people: list[Detection], teacher_name: str = ""):
    if not people:
        return None

    def score(detection):
        x1, y1, x2, y2 = detection.box
        width = max(1, x2 - x1)
        height = max(1, y2 - y1)
        upper_y1 = max(0, y1 + int(height * 0.12))
        upper_y2 = max(0, min(y2, y1 + int(height * 0.58)))
        center_x1 = max(0, x1 + int(width * 0.18))
        center_x2 = max(0, x2 - int(width * 0.18))
        torso = frame[upper_y1:upper_y2, center_x1:center_x2]
        white_score = 0.0
        blue_score = 0.0
        dark_score = 0.0
        if torso.size:
            hsv = cv2.cvtColor(torso, cv2.COLOR_BGR2HSV)
            white_mask = cv2.inRange(hsv, (0, 0, 130), (180, 95, 255))
            blue_mask = cv2.inRange(hsv, (90, 35, 35), (135, 255, 255))
            dark_mask = cv2.inRange(hsv, (0, 0, 0), (180, 255, 70))
            white_score = cv2.countNonZero(white_mask) / max(1, torso.shape[0] * torso.shape[1])
            blue_score = cv2.countNonZero(blue_mask) / max(1, torso.shape[0] * torso.shape[1])
            dark_score = cv2.countNonZero(dark_mask) / max(1, torso.shape[0] * torso.shape[1])

        aspect = height / width
        standing_score = min(aspect / 2.2, 1.25)
        bottom_score = min(y2 / frame.shape[0], 1.0)
        seated_penalty = 45 if y2 > 1040 and height < 340 else 0
        empty_blue_penalty = blue_score * 90
        dark_clothes_penalty = dark_score * 45
        return (
            white_score * 520
            + standing_score * 85
            + bottom_score * 45
            + detection.confidence * 55
            - empty_blue_penalty
            - dark_clothes_penalty
            - seated_penalty
        )

    return max(people, key=score).box


def draw_overlay(frame, detections, faces):
    for detection in detections:
        x1, y1, x2, y2 = detection.box
        color = (0, 255, 0) if detection.label == "person" else (0, 165, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            frame,
            f"{detection.label} {detection.confidence:.2f}",
            (x1, max(20, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
        )

    for face in faces:
        x, y, w, h = face.box
        color = (255, 0, 255) if face.name else (180, 180, 180)
        cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
        label = face.name or "unknown"
        cv2.putText(frame, label, (x, max(20, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color, 2)


if __name__ == "__main__":
    main()
