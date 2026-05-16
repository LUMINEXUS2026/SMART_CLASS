from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

from app.models import Lesson, LessonParticipant, LessonTextbookState, Student
from app.routes.guards import roles_required

student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.get("/dashboard")
@roles_required("student")
def dashboard():
    student = Student.query.filter_by(user_id=current_user.id).first()
    active_query = Lesson.query.filter_by(status="active")
    if student:
        active_query = active_query.filter_by(group_id=student.group_id)
    else:
        active_query = active_query.filter(Lesson.group_id.is_(None))
    active_lessons = active_query.order_by(Lesson.starts_at.desc()).all()
    my_participations = LessonParticipant.query.filter_by(student_id=current_user.id).all()
    joined_ids = {p.lesson_id for p in my_participations}
    textbook_states = (
        {
            state.lesson_id: state
            for state in LessonTextbookState.query.filter(
                LessonTextbookState.lesson_id.in_([lesson.id for lesson in active_lessons])
            ).all()
        }
        if active_lessons
        else {}
    )
    return render_template(
        "student/dashboard.html",
        active_lessons=active_lessons,
        joined_ids=joined_ids,
        textbook_states=textbook_states,
    )


@student_bp.get("/lesson/<int:lesson_id>")
@roles_required("student")
def lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.status != "active":
        return redirect(url_for("student.dashboard"))
    student = Student.query.filter_by(user_id=current_user.id).first()
    if lesson.group_id and (not student or student.group_id != lesson.group_id):
        return redirect(url_for("student.dashboard"))
    textbook_state = LessonTextbookState.query.filter_by(lesson_id=lesson.id).first()
    return render_template("student/lesson.html", lesson=lesson, textbook_state=textbook_state)

