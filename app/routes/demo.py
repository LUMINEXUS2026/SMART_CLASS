from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from app.extensions import db
from app.models import Lesson, LessonEvent, Student, TextbookActivity, User
from app.routes.textbook import flatten_pages, load_toc, render_markdown, resolve_page_path
from app.services.event_service import create_event
from app.services.lesson_service import finish_lesson
from app.routes.teacher import readable_lesson_subject, readable_lesson_title

demo_bp = Blueprint("demo", __name__, url_prefix="/demo")


@demo_bp.get("")
def home():
    lesson, student = ensure_demo_data()
    return render_template("demo.html", lesson=lesson, student=student)


@demo_bp.get("/teacher/<int:lesson_id>")
def teacher_live(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    events = (
        LessonEvent.query.filter_by(lesson_id=lesson.id)
        .order_by(LessonEvent.created_at.desc())
        .limit(100)
        .all()
    )
    group_students = Student.query.filter_by(group_id=lesson.group_id).order_by(Student.full_name.asc()).all() if lesson.group_id else []
    return render_template(
        "teacher/lesson_live.html",
        lesson=lesson,
        lesson_title=readable_lesson_title(lesson),
        lesson_subject=readable_lesson_subject(lesson),
        participants=lesson.participants,
        group_students=group_students,
        events=events,
        activity_by_student={student.user_id: 0 for student in group_students},
        events_url=url_for("demo.demo_events", lesson_id=lesson.id),
        finish_url=url_for("demo.finish_demo_lesson", lesson_id=lesson.id),
    )


@demo_bp.post("/teacher/<int:lesson_id>/finish")
def finish_demo_lesson(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    finish_lesson(lesson)
    db.session.commit()
    return redirect(url_for("reports.lesson_report", lesson_id=lesson.id))


@demo_bp.get("/student/<int:lesson_id>/page/<int:page_index>")
def student_book(lesson_id, page_index):
    lesson = Lesson.query.get_or_404(lesson_id)
    _, student = ensure_demo_data(lesson)
    pages = flatten_pages(load_toc())
    if page_index < 0 or page_index >= len(pages):
        page_index = 0
    item = pages[page_index]
    html = render_markdown(resolve_page_path(page_index, item))
    create_event(lesson.id, student.id, "student_arrived", "web", {"demo": True})
    db.session.commit()
    return render_template(
        "textbook/book.html",
        lesson=lesson,
        student_name=student.name,
        page=item,
        page_index=page_index,
        total=len(pages),
        pages=pages,
        content=html,
        prev_index=page_index - 1 if page_index > 0 else None,
        next_index=page_index + 1 if page_index < len(pages) - 1 else None,
        demo_mode=True,
        activity_url=url_for("demo.demo_textbook_activity", lesson_id=lesson.id),
        status_url=url_for("demo.demo_status", lesson_id=lesson.id),
    )


@demo_bp.get("/lessons/<int:lesson_id>/events")
def demo_events(lesson_id):
    events = (
        LessonEvent.query.filter_by(lesson_id=lesson_id)
        .order_by(LessonEvent.created_at.desc())
        .limit(100)
        .all()
    )
    return jsonify([
        {
            "id": event.id,
            "event_type": event.event_type,
            "student": event.student.name if event.student else None,
            "source": event.source,
            "created_at": event.created_at.isoformat(),
        }
        for event in events
    ])


@demo_bp.get("/lessons/<int:lesson_id>/status")
def demo_status(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    return jsonify({"id": lesson.id, "status": lesson.status})


@demo_bp.post("/lessons/<int:lesson_id>/textbook-activity")
def demo_textbook_activity(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    _, student = ensure_demo_data(lesson)
    data = request.get_json(force=True)
    activity = TextbookActivity(
        lesson_id=lesson.id,
        student_id=student.id,
        page_index=int(data.get("page_index", 0)),
        action=data.get("action", "unknown"),
        duration_sec=int(data.get("duration_sec", 0)),
        payload_json="{}",
    )
    db.session.add(activity)
    action = data.get("action")
    if action == "tab_hidden":
        create_event(lesson.id, student.id, "student_left_during_lesson", "web", {"reason": "tab_hidden"})
    elif action == "tab_visible":
        create_event(lesson.id, student.id, "student_returned_during_lesson", "web", {"reason": "tab_visible"})
    elif action == "help_requested":
        create_event(lesson.id, student.id, "difficulty_indicator_detected", "web", {"reason": "help_requested"})
    db.session.commit()
    return jsonify({"ok": True})


def ensure_demo_data(lesson=None):
    teacher = User.query.filter_by(email="teacher@example.com").first()
    student = User.query.filter_by(email="student@example.com").first()
    if not teacher:
        teacher = User(
            email="teacher@example.com",
            name="Учитель",
            role="teacher",
            password_hash=generate_password_hash("password"),
        )
        db.session.add(teacher)
    if not student:
        student = User(
            email="student@example.com",
            name="Ученик",
            role="student",
            password_hash=generate_password_hash("password"),
        )
        db.session.add(student)
    db.session.flush()
    if lesson is None:
        lesson = Lesson.query.filter_by(status="active").order_by(Lesson.starts_at.desc()).first()
    if lesson is None:
        lesson = Lesson(title="Демо-урок: Математика 6 класс", subject="Математика", teacher_id=teacher.id)
        db.session.add(lesson)
        db.session.flush()
    if not any(p.student_id == student.id for p in lesson.participants):
        from app.models import LessonParticipant

        db.session.add(LessonParticipant(lesson_id=lesson.id, student_id=student.id))
    db.session.commit()
    return lesson, student
