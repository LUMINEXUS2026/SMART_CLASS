from datetime import datetime, timezone

from app.extensions import db
from app.models import LessonParticipant
from app.services.event_service import create_event


def join_lesson(lesson, student):
    participant = LessonParticipant.query.filter_by(lesson_id=lesson.id, student_id=student.id).first()
    if participant:
        return participant
    participant = LessonParticipant(lesson_id=lesson.id, student_id=student.id)
    db.session.add(participant)

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    minutes_since_start = (now - lesson.starts_at).total_seconds() / 60
    if minutes_since_start > lesson.late_after_minutes:
        create_event(lesson.id, student.id, "student_late", "web", {"minutes_since_start": round(minutes_since_start)})
    return participant


def finish_lesson(lesson):
    lesson.status = "finished"
    lesson.ends_at = datetime.now(timezone.utc).replace(tzinfo=None)
    for participant in lesson.participants:
        if participant.left_at is None:
            participant.left_at = lesson.ends_at

