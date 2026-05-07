import json

from app.extensions import db
from app.models import LessonEvent
from app.services.event_schema import ALLOWED_EVENT_TYPES, EVENT_DEFINITIONS, normalize_event_payload


def create_event(lesson_id, student_id, event_type, source, payload):
    if event_type not in ALLOWED_EVENT_TYPES:
        raise ValueError(f"Unknown lesson event: {event_type}")
    normalized_payload = normalize_event_payload(
        lesson_id=lesson_id,
        student_id=student_id,
        event_type=event_type,
        source=source,
        payload=payload,
    )
    review_policy = EVENT_DEFINITIONS[event_type]["review"]
    review_status = "pending" if normalized_payload["manual_review_required"] or review_policy == "manual" else "confirmed"
    event = LessonEvent(
        lesson_id=lesson_id,
        student_id=student_id,
        event_type=event_type,
        source=source,
        payload_json=json.dumps(normalized_payload, ensure_ascii=False),
        review_status=review_status,
    )
    db.session.add(event)
    return event


def parse_payload(event):
    try:
        return json.loads(event.payload_json or "{}")
    except json.JSONDecodeError:
        return {}
