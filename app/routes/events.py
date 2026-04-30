from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.extensions import db
from app.models import Lesson, LessonEvent, TextbookActivity, User
from app.services.event_service import ALLOWED_EVENT_TYPES, create_event

events_bp = Blueprint("events", __name__, url_prefix="/api")


@events_bp.get("/lessons/<int:lesson_id>/events")
@login_required
def list_events(lesson_id):
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


@events_bp.post("/lessons/<int:lesson_id>/events")
@login_required
def create_web_event(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.status != "active":
        return jsonify({"ok": False, "error": "lesson_finished"}), 409
    data = request.get_json(force=True)
    event_type = data.get("event_type")
    if event_type not in ALLOWED_EVENT_TYPES:
        return jsonify({"ok": False, "error": "unknown_event_type"}), 400
    event = create_event(lesson.id, current_user.id, event_type, "web", data.get("payload") or {})
    db.session.commit()
    return jsonify({"ok": True, "event_id": event.id})


@events_bp.post("/camera/events")
def create_camera_event():
    token = request.headers.get("X-Camera-Token", "")
    if token != current_app.config["CAMERA_EVENT_TOKEN"]:
        return jsonify({"ok": False, "error": "unauthorized"}), 401
    data = request.get_json(force=True)
    lesson = Lesson.query.get_or_404(int(data.get("lesson_id")))
    event_type = data.get("event_type")
    if event_type not in ALLOWED_EVENT_TYPES:
        return jsonify({"ok": False, "error": "unknown_event_type"}), 400
    student_id = data.get("student_id")
    student_name = data.get("student_name")
    if not student_id and student_name:
        user = User.query.filter_by(name=student_name, role="student").first()
        student_id = user.id if user else None
    event = create_event(lesson.id, student_id, event_type, "camera", data.get("payload") or {})
    db.session.commit()
    return jsonify({"ok": True, "event_id": event.id})


@events_bp.post("/lessons/<int:lesson_id>/textbook-activity")
@login_required
def textbook_activity(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    if lesson.status != "active":
        return jsonify({"ok": False, "error": "lesson_finished"}), 409
    data = request.get_json(force=True)
    activity = TextbookActivity(
        lesson_id=lesson.id,
        student_id=current_user.id,
        page_index=int(data.get("page_index", 0)),
        action=data.get("action", "unknown"),
        duration_sec=int(data.get("duration_sec", 0)),
        payload_json="{}",
    )
    db.session.add(activity)
    if data.get("action") == "tab_hidden":
        create_event(lesson.id, current_user.id, "student_left_during_lesson", "web", {"reason": "tab_hidden"})
    elif data.get("action") == "tab_visible":
        create_event(lesson.id, current_user.id, "student_returned_during_lesson", "web", {"reason": "tab_visible"})
    elif data.get("action") == "help_requested":
        create_event(lesson.id, current_user.id, "difficulty_indicator_detected", "web", {"reason": "help_requested"})
    db.session.commit()
    return jsonify({"ok": True})

