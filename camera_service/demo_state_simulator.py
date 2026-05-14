from __future__ import annotations

import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path


STATE_PATH = Path("instance/camera_state/classroom_5.json")
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
VIDEO_DURATION = 316
TEACHER_KEYFRAMES = [
    (0, (1185, 365, 235, 430)),
    (45, (1235, 385, 230, 425)),
    (95, (1265, 382, 225, 430)),
    (150, (1295, 388, 220, 430)),
    (210, (1320, 384, 215, 435)),
    (248, (1310, 386, 215, 435)),
    (285, (1275, 390, 220, 428)),
    (316, (1185, 365, 235, 430)),
]


def moving_box(x: int, y: int, w: int, h: int, phase: float, scale: float = 1.0) -> list[int]:
    return [
        int(x + math.sin(phase) * 10 * scale),
        int(y + math.cos(phase * 0.8) * 6 * scale),
        w,
        h,
    ]


def interpolate_box(video_time: float, keyframes: list[tuple[int, tuple[int, int, int, int]]]) -> list[int]:
    for index, (time_a, box_a) in enumerate(keyframes[:-1]):
        time_b, box_b = keyframes[index + 1]
        if time_a <= video_time <= time_b:
            progress = (video_time - time_a) / max(time_b - time_a, 1)
            eased = progress * progress * (3 - 2 * progress)
            return [
                int(box_a[item] + (box_b[item] - box_a[item]) * eased)
                for item in range(4)
            ]
    return list(keyframes[-1][1])


def teacher_box_for(video_time: float, phase: float) -> list[int]:
    x, y, w, h = interpolate_box(video_time, TEACHER_KEYFRAMES)
    return moving_box(x, y, w, h, phase, 0.45)


def build_state(started_at: float) -> dict:
    elapsed = time.time() - started_at
    video_time = elapsed % VIDEO_DURATION
    phase = elapsed / 2.4
    students = [
        ("Не распознанный человек 01", 0.89, moving_box(480, 812, 310, 268, phase), 96),
        ("Не распознанный человек 02", 0.82, moving_box(500, 670, 178, 142, phase + 0.8), 90),
        ("Не распознанный человек 03", 0.69, moving_box(1360, 430, 108, 164, phase + 1.4), 86),
        ("Не распознанный человек 04", 0.44, moving_box(1210, 535, 150, 170, phase + 2.1), 80),
    ]
    detections = [
        {
            "label": "person",
            "role": "teacher",
            "name": "Киреева Ирина",
            "confidence": 0.85,
            "box": teacher_box_for(video_time, phase + 0.3),
            "detail": "teacher tracking",
        }
    ]
    for index, (name, confidence, box, attention) in enumerate(students, start=1):
        detections.append(
            {
                "label": "person",
                "role": "student",
                "name": name,
                "confidence": confidence,
                "box": box,
                "detail": "AI person tracking",
                "track_id": f"student-{index:02d}",
                "attention": attention,
                "status": "visible",
            }
        )

    return {
        "camera": "Демо-видео",
        "room": "Кабинет 5",
        "lesson": "Английский язык",
        "teacher": "Киреева Ирина",
        "status": "running",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "video_time_sec": round(video_time, 2),
        "attention": 88,
        "people_count": len(detections),
        "phones_count": 0,
        "frame_width": FRAME_WIDTH,
        "frame_height": FRAME_HEIGHT,
        "detections": detections,
        "recognitions": detections,
        "student_attention": [
            {"student": name, "attention": attention, "status": "visible"}
            for name, _, _, attention in students
        ],
        "events": [],
    }


def write_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp_path = STATE_PATH.with_name(f"{STATE_PATH.stem}.{os.getpid()}.tmp")
    temp_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(STATE_PATH)


def main() -> None:
    started_at = time.time()
    while True:
        write_state(build_state(started_at))
        time.sleep(0.35)


if __name__ == "__main__":
    main()
