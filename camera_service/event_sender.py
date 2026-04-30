import requests


class EventSender:
    def __init__(self, backend_url, token, timeout=2.0):
        self.backend_url = backend_url.rstrip("/")
        self.token = token
        self.timeout = timeout

    def send(self, lesson_id, event_type, student_id=None, student_name=None, payload=None):
        response = requests.post(
            f"{self.backend_url}/api/camera/events",
            headers={"X-Camera-Token": self.token},
            json={
                "lesson_id": lesson_id,
                "event_type": event_type,
                "student_id": student_id,
                "student_name": student_name,
                "payload": payload or {},
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

