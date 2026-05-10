from datetime import datetime

from flask import Blueprint, current_app, jsonify, request

from app.extensions import db
from app.models import Lesson, LessonParticipant
from app.services.attendance_service import create_attendance_event
from app.services.event_service import create_event

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")

LOW_CONFIDENCE_THRESHOLD = 0.65


@ai_bp.post("/detections")
def detections():
    token = request.headers.get("X-Camera-Token", "")
    if token != current_app.config["CAMERA_EVENT_TOKEN"]:
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    data = request.get_json(force=True)
    lesson = Lesson.query.get_or_404(int(data.get("lesson_id")))
    user_id = data.get("user_id") or data.get("student_id")
    confidence = float(data.get("confidence", 0))
    detected = bool(data.get("detected", False))
    manual_review_required = confidence < LOW_CONFIDENCE_THRESHOLD
    status = "present" if detected and not manual_review_required else "uncertain" if detected else "absent"

    if user_id:
        participant = LessonParticipant.query.filter_by(lesson_id=lesson.id, student_id=int(user_id)).first()
        if not participant:
            participant = LessonParticipant(lesson_id=lesson.id, student_id=int(user_id))
            db.session.add(participant)
        if detected and not manual_review_required:
            participant.attendance_status = "present"
            participant.is_present_by_camera = True
        elif manual_review_required:
            participant.attendance_status = "uncertain"
            participant.manual_note = "AI confidence is low; teacher review required"
        else:
            participant.attendance_status = "absent"
        create_attendance_event(int(user_id), lesson.id, status, "ai")

    event_type = "detected" if detected else "absent"
    event = create_event(
        lesson.id,
        int(user_id) if user_id else None,
        event_type,
        "ai",
        {
            "detected": detected,
            "confidence": confidence,
            "timestamp": data.get("timestamp") or datetime.utcnow().isoformat(),
            "status": status,
            "camera": data.get("camera"),
            "lesson_id": lesson.id,
            "user_id": user_id,
            "manual_review_required": manual_review_required,
            "raw": data.get("raw") or {},
        },
    )
    if manual_review_required:
        create_event(
            lesson.id,
            int(user_id) if user_id else None,
            "warning",
            "ai",
            {
                "status": "ai_low_confidence",
                "confidence": confidence,
                "manual_review_required": True,
                "linked_event_id": event.id,
            },
        )
    db.session.commit()
    return jsonify(
        {
            "ok": True,
            "event_id": event.id,
            "detected": detected,
            "confidence": confidence,
            "manual_review_required": manual_review_required,
            "lesson_id": lesson.id,
            "user_id": int(user_id) if user_id else None,
        }
    )


@ai_bp.post("/explain")
def explain():
    data = request.get_json(force=True)
    topic = (data.get("topic_title") or "Математика 6 класс").strip()
    task = (data.get("task_text") or "текущее задание").strip()
    question = (data.get("question") or "").strip()

    answer = (
        f"**Тема:** {topic}\n\n"
        "1. Сначала найди, что известно в условии.\n"
        "2. Потом запиши, что нужно доказать или посчитать.\n"
        "3. Решай маленькими шагами и проверяй каждый шаг.\n\n"
        f"**Похожая ситуация:** возьми такое же задание, но с другими числами или словами. "
        "Разбери его по шагам, а своё задание реши самостоятельно.\n\n"
        f"**Твой вопрос:** {question or 'пока не указан'}\n\n"
        "Я не пишу готовый ответ, а помогаю понять способ решения."
    )
    return jsonify({"ok": True, "text": answer, "task": task[:800]})
