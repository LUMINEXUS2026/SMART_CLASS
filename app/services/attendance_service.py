from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import Lesson, LessonParticipant, Student
from app.services.event_service import create_event


def active_lesson_for_student(user):
    profile = Student.query.filter_by(user_id=user.id).first()
    if not profile:
        return None
    return (
        Lesson.query.filter_by(group_id=profile.group_id, status="active")
        .order_by(Lesson.starts_at.desc())
        .first()
    )


def attendance_status_for(lesson, now=None):
    now = now or datetime.now()
    starts_at = lesson.starts_at
    if not starts_at:
        return "arrived"
    late_after_minutes = lesson.late_after_minutes or 10
    minutes_after_start = (now - starts_at).total_seconds() / 60
    return "late" if minutes_after_start > late_after_minutes else "arrived"


def record_student_login_presence(user):
    lesson = active_lesson_for_student(user)
    if not lesson:
        return None

    status = attendance_status_for(lesson)
    participant = LessonParticipant.query.filter_by(lesson_id=lesson.id, student_id=user.id).first()
    was_new = participant is None
    if not participant:
        participant = LessonParticipant(
            lesson_id=lesson.id,
            student_id=user.id,
            attendance_status=status,
            is_present_by_camera=False,
        )
        db.session.add(participant)
    else:
        participant.attendance_status = status if participant.attendance_status == "absent" else participant.attendance_status

    create_event(
        lesson.id,
        user.id,
        "login",
        "auth",
        {
            "status": status,
            "participant_id": participant.id,
            "auto_attendance": True,
        },
    )
    if was_new:
        create_event(
            lesson.id,
            user.id,
            "student_arrived" if status == "arrived" else "student_late",
            "auth",
            {
                "status": status,
                "participant_id": participant.id,
                "reason": "student_login",
            },
        )
    return participant


def record_student_logout(user):
    lesson = active_lesson_for_student(user)
    if not lesson:
        return None
    return create_event(
        lesson.id,
        user.id,
        "logout",
        "auth",
        {
            "status": "left_system",
            "reason": "user_logout",
        },
    )
