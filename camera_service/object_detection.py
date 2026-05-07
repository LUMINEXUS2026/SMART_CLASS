from __future__ import annotations

from dataclasses import dataclass


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
        from ultralytics import YOLO

        self.model = YOLO(model_path)
        self.confidence = confidence
        self.imgsz = imgsz

    def detect(self, frame) -> list[Detection]:
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
