from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class FaceMatch:
    name: str | None
    confidence: float
    box: tuple[int, int, int, int]


class FaceRecognitionAdapter:
    """LBPH face recognizer for a folder-based face database.

    Expected structure:

    faces_db/
      Иванов Иван/
        1.jpg
        2.jpg
      Петрова Анна/
        1.png

    Lower confidence is better for OpenCV LBPH. `threshold` is the maximum
    accepted confidence; values around 65-85 are reasonable for a first MVP,
    but real classrooms need calibration and consent.
    """

    def __init__(self, faces_dir: str | Path, threshold: float = 78.0):
        self.faces_dir = Path(faces_dir)
        self.threshold = threshold
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self.recognizer = None
        self.labels: dict[int, str] = {}
        self._train()

    @property
    def ready(self) -> bool:
        return self.recognizer is not None and bool(self.labels)

    def _train(self) -> None:
        if not self.faces_dir.exists():
            return
        if not hasattr(cv2, "face"):
            raise RuntimeError(
                "OpenCV face module is missing. Install opencv-contrib-python."
            )

        images: list[np.ndarray] = []
        labels: list[int] = []
        label_id = 0

        for person_dir in sorted(path for path in self.faces_dir.iterdir() if path.is_dir()):
            person_images = []
            for image_path in sorted(person_dir.glob("*")):
                if image_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
                    continue
                image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
                if image is None:
                    continue
                faces = self.face_cascade.detectMultiScale(image, scaleFactor=1.1, minNeighbors=5)
                if len(faces) == 0:
                    person_images.append(cv2.resize(image, (160, 160)))
                    continue
                x, y, w, h = max(faces, key=lambda box: box[2] * box[3])
                person_images.append(cv2.resize(image[y : y + h, x : x + w], (160, 160)))

            if person_images:
                self.labels[label_id] = person_dir.name
                images.extend(person_images)
                labels.extend([label_id] * len(person_images))
                label_id += 1

        if not images:
            return

        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.recognizer.train(images, np.array(labels, dtype=np.int32))

    def recognize(self, frame) -> list[FaceMatch]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        matches: list[FaceMatch] = []

        for x, y, w, h in faces:
            name = None
            confidence = 999.0
            if self.ready:
                roi = cv2.resize(gray[y : y + h, x : x + w], (160, 160))
                label_id, confidence = self.recognizer.predict(roi)
                if confidence <= self.threshold:
                    name = self.labels.get(label_id)
            matches.append(FaceMatch(name=name, confidence=float(confidence), box=(x, y, w, h)))

        return matches
