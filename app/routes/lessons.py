from flask import Blueprint, jsonify, redirect, request, url_for
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Lesson, LessonParticipant, LessonTextbookState, Student
from app.routes.guards import roles_required
from app.services.event_service import create_event
from app.services.lesson_service import finish_lesson, join_lesson

lessons_bp = Blueprint("lessons", __name__, url_prefix="/lessons")


@lessons_bp.post("")
@roles_required("teacher")
def create_lesson():
    title = request.form.get("title", "").strip() or "Новый урок"
    subject = request.form.get("subject", "").strip() or "Математика"
    group_id = request.form.get("group_id", type=int)
    lesson = Lesson(title=title, subject=subject, teacher_id=current_user.id, group_id=group_id)
    db.session.add(lesson)
    db.session.commit()
    return redirect(url_for("teacher.lesson_live", lesson_id=lesson.id))


@lessons_bp.post("/<int:lesson_id>/join")
@roles_required("student")
def join(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.status != "active":
        return redirect(url_for("student.dashboard"))
    student = Student.query.filter_by(user_id=current_user.id).first()
    if lesson.group_id and (not student or student.group_id != lesson.group_id):
        return redirect(url_for("student.dashboard"))
    participant = join_lesson(lesson, current_user)
    create_event(lesson.id, current_user.id, "student_arrived", "web", {"participant_id": participant.id})
    db.session.commit()
    return redirect(url_for("student.lesson", lesson_id=lesson.id))


@lessons_bp.post("/<int:lesson_id>/finish")
@roles_required("teacher")
def finish(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.teacher_id != current_user.id:
        return redirect(url_for("teacher.dashboard"))
    finish_lesson(lesson)
    db.session.commit()
    return redirect(url_for("reports.lesson_report", lesson_id=lesson.id))


@lessons_bp.get("/<int:lesson_id>/status")
@login_required
def status(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    participant_count = LessonParticipant.query.filter_by(lesson_id=lesson.id).count()
    state = LessonTextbookState.query.filter_by(lesson_id=lesson.id).first()
    return jsonify(
        {
            "id": lesson.id,
            "status": lesson.status,
            "participants": participant_count,
            "textbook": {
                "assigned_page_index": state.assigned_page_index if state else None,
                "assigned_title": state.assigned_title if state else "",
                "study_mode": state.study_mode if state else "textbook",
                "updated_at": state.updated_at.isoformat() if state else None,
            },
        }
    )
