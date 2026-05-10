from __future__ import annotations

from datetime import datetime

from app.extensions import db
from app.models import AttendanceEvent, Lesson, LessonParticipant, Student
from app.services.event_service import create_event

ATTENDANCE_STATUSES = {"present", "absent", "late", "manual_confirmed", "uncertain"}


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
        return "present"
    late_after_minutes = lesson.late_after_minutes or 5
    minutes_after_start = (now - starts_at).total_seconds() / 60
    return "late" if minutes_after_start > late_after_minutes else "present"


def create_attendance_event(user_id, lesson_id, status, source, confirmed_by_teacher_id=None, timestamp=None):
    if status not in ATTENDANCE_STATUSES:
        raise ValueError(f"Unknown attendance status: {status}")
    event = AttendanceEvent(
        user_id=user_id,
        lesson_id=lesson_id,
        timestamp=timestamp or datetime.now(),
        status=status,
        source=source,
        confirmed_by_teacher_id=confirmed_by_teacher_id,
    )
    db.session.add(event)
    db.session.flush()
    return event


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
    create_attendance_event(user.id, lesson.id, status, "login")
    if was_new:
        create_event(
            lesson.id,
            user.id,
            "student_arrived" if status == "present" else "student_late",
            "auth",
            {
                "status": status,
                "participant_id": participant.id,
                "reason": "student_login",
            },
        )
    return participant


def record_teacher_attendance_update(lesson, student_id, status, teacher_id):
    if status not in ATTENDANCE_STATUSES:
        raise ValueError(f"Unknown attendance status: {status}")
    participant = LessonParticipant.query.filter_by(lesson_id=lesson.id, student_id=student_id).first()
    if not participant:
        participant = LessonParticipant(lesson_id=lesson.id, student_id=student_id)
        db.session.add(participant)
    participant.attendance_status = status
    participant.manual_note = "Changed by teacher"
    attendance_event = create_attendance_event(
        student_id,
        lesson.id,
        status,
        "teacher",
        confirmed_by_teacher_id=teacher_id,
    )
    create_event(
        lesson.id,
        student_id,
        "attendance_manual_update",
        "teacher",
        {
            "status": status,
            "attendance_event_id": attendance_event.id,
            "participant_id": participant.id,
            "confirmed_by_teacher_id": teacher_id,
            "manual_review_required": False,
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
