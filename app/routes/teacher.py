from collections import Counter

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user

from app.extensions import db
from app.models import (
    Group,
    Lesson,
    LessonEvent,
    LessonParticipant,
    Student,
    TeacherGroupLink,
    TextbookActivity,
)
from app.routes.guards import roles_required

teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


@teacher_bp.get("/dashboard")
@roles_required("teacher")
def dashboard():
    group_ids = [link.group_id for link in TeacherGroupLink.query.filter_by(teacher_id=current_user.id).all()]
    lessons = (
        Lesson.query.filter(Lesson.teacher_id == current_user.id, Lesson.group_id.in_(group_ids) if group_ids else Lesson.group_id.is_(None))
        .order_by(Lesson.starts_at.desc())
        .limit(20)
        .all()
    )
    groups = Group.query.filter(Group.id.in_(group_ids)).all() if group_ids else []
    event_counts = Counter()
    for lesson in lessons:
        event_counts.update(event.event_type for event in lesson.events)
    return render_template("teacher/dashboard.html", lessons=lessons, groups=groups, event_counts=event_counts)


@teacher_bp.get("/lesson/<int:lesson_id>")
@roles_required("teacher")
def lesson_live(lesson_id):
    lesson = get_teacher_lesson_or_404(lesson_id)
    participants = LessonParticipant.query.filter_by(lesson_id=lesson.id).all()
    group_students = Student.query.filter_by(group_id=lesson.group_id).order_by(Student.full_name.asc()).all() if lesson.group_id else []
    events = (
        LessonEvent.query.filter_by(lesson_id=lesson.id)
        .order_by(LessonEvent.created_at.desc())
        .limit(100)
        .all()
    )
    activity_by_student = {
        student.user_id: TextbookActivity.query.filter_by(lesson_id=lesson.id, student_id=student.user_id).count()
        for student in group_students
    }
    return render_template(
        "teacher/lesson_live.html",
        lesson=lesson,
        participants=participants,
        group_students=group_students,
        events=events,
        activity_by_student=activity_by_student,
    )


@teacher_bp.post("/events/<int:event_id>/review")
@roles_required("teacher")
def review_event(event_id):
    event = LessonEvent.query.get_or_404(event_id)
    get_teacher_lesson_or_404(event.lesson_id)
    action = request.form.get("action")
    if action not in {"confirmed", "rejected"}:
        abort(400)
    event.review_status = action
    event.reviewed_by_id = current_user.id
    db.session.commit()
    return redirect(url_for("teacher.lesson_live", lesson_id=event.lesson_id))


@teacher_bp.post("/lesson/<int:lesson_id>/attendance")
@roles_required("teacher")
def update_attendance(lesson_id):
    lesson = get_teacher_lesson_or_404(lesson_id)
    student_id = int(request.form.get("student_id"))
    status = request.form.get("status")
    if status not in {"arrived", "late", "absent", "left", "returned", "left_early"}:
        abort(400)
    participant = LessonParticipant.query.filter_by(lesson_id=lesson.id, student_id=student_id).first()
    if not participant:
        participant = LessonParticipant(lesson_id=lesson.id, student_id=student_id)
        db.session.add(participant)
    participant.attendance_status = status
    participant.manual_note = "Исправлено учителем"
    db.session.commit()
    return redirect(url_for("teacher.lesson_live", lesson_id=lesson.id))


def get_teacher_lesson_or_404(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.teacher_id != current_user.id:
        abort(403)
    return lesson
