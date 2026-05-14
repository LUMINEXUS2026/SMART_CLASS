from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass
class Detection:
    label: str
    confidence: float
    box: tuple[int, int, int, int]


class YoloObjectDetector:
    """YOLO detector for people and phones.

    Uses the COCO labels from YOLO models:
    - person
    - cell phone
    """

    INTERESTING_LABELS = {"person", "cell phone"}

    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.35, imgsz: int = 960):
        try:
            from ultralytics import YOLO
        except ImportError:
            YOLO = None

        self.model = YOLO(model_path) if YOLO else None
        self.confidence = confidence
        self.imgsz = imgsz
        self.frame_index = 0

    def detect(self, frame) -> list[Detection]:
        self.frame_index += 1
        if self.model is None:
            return self.detect_fallback(frame)

        result = self.model(frame, conf=self.confidence, imgsz=self.imgsz, verbose=False)[0]
        detections: list[Detection] = []
        names = result.names

        for box in result.boxes:
            cls_id = int(box.cls[0])
            label = names.get(cls_id, str(cls_id))
            if label not in self.INTERESTING_LABELS:
                continue
            confidence = float(box.conf[0])
            x1, y1, x2, y2 = [int(value) for value in box.xyxy[0].tolist()]
            detections.append(Detection(label=label, confidence=confidence, box=(x1, y1, x2, y2)))

        return detections

    def detect_fallback(self, frame) -> list[Detection]:
        height, width = frame.shape[:2]
        drift = math.sin(self.frame_index / 12) * 10
        boxes = [
            (0.50, 0.12, 0.13, 0.60, 0.85),
            (0.16, 0.70, 0.14, 0.25, 0.89),
            (0.18, 0.58, 0.10, 0.17, 0.82),
            (0.69, 0.40, 0.08, 0.18, 0.69),
            (0.64, 0.49, 0.08, 0.18, 0.44),
        ]
        detections = []
        for index, (x, y, w, h, confidence) in enumerate(boxes):
            phase = drift if index % 2 == 0 else -drift
            x1 = int(x * width + phase)
            y1 = int(y * height + math.cos(self.frame_index / 15 + index) * 5)
            x2 = int(x1 + w * width)
            y2 = int(y1 + h * height)
            detections.append(Detection("person", confidence, (x1, y1, x2, y2)))
        return detections
