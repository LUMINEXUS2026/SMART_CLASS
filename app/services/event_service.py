import json

from app.extensions import db
from app.models import LessonEvent

ALLOWED_EVENT_TYPES = {
    "student_arrived",
    "student_late",
    "student_left_during_lesson",
    "student_returned_during_lesson",
    "student_left_early",
    "distraction_detected",
    "difficulty_indicator_detected",
    "lesson_summary_ready",
}


def create_event(lesson_id, student_id, event_type, source, payload):
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f"Unknown lesson event: {event_type}")
    event = LessonEvent(
        lesson_id=lesson_id,
        student_id=student_id,
        event_type=event_type,
        source=source,
        payload_json=json.dumps(payload or {}, ensure_ascii=False),
    )
    db.session.add(event)
    return event

