from __future__ import annotations

from datetime import datetime, timezone

SCHEMA_VERSION = "smart-class.event.v1"

EVENT_DEFINITIONS = {
    "login": {
        "description": "User entered the system or lesson module.",
        "review": "auto",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "logout": {
        "description": "User left the system or lesson module.",
        "review": "auto",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "detected": {
        "description": "AI detected a person or known user in the camera frame.",
        "review": "manual_if_low_confidence",
        "required": ["lesson_id", "user_id", "timestamp", "confidence"],
    },
    "absent": {
        "description": "Student is not confirmed as present.",
        "review": "manual",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "inactive": {
        "description": "Student had a long inactivity pause in the learning module.",
        "review": "auto",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "warning": {
        "description": "Neutral warning for teacher review, without automatic punishment.",
        "review": "manual",
        "required": ["lesson_id", "timestamp", "status"],
    },
    "student_arrived": {
        "description": "Student presence was confirmed by login, teacher, or AI.",
        "review": "auto",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "student_late": {
        "description": "Student joined after the configured late threshold.",
        "review": "auto",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "student_left_during_lesson": {
        "description": "Student may have left the learning tab or classroom during a lesson.",
        "review": "manual",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "student_returned_during_lesson": {
        "description": "Student returned to the learning tab or classroom.",
        "review": "auto",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "student_left_early": {
        "description": "Teacher confirmed that a student left before the lesson ended.",
        "review": "manual",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "distraction_detected": {
        "description": "Observable distraction signal, for example a phone detection.",
        "review": "manual",
        "required": ["lesson_id", "timestamp", "confidence"],
    },
    "difficulty_indicator_detected": {
        "description": "Student requested help or showed a difficulty signal in the module.",
        "review": "auto",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "textbook_action": {
        "description": "Learning module action: open, start task, finish task, pause, page change.",
        "review": "auto",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
    "lesson_summary_ready": {
        "description": "Lesson summary or analytics snapshot became available.",
        "review": "auto",
        "required": ["lesson_id", "timestamp", "status"],
    },
    "attendance_manual_update": {
        "description": "Teacher manually corrected a student's attendance status.",
        "review": "auto",
        "required": ["lesson_id", "user_id", "timestamp", "status"],
    },
}

ALLOWED_EVENT_TYPES = set(EVENT_DEFINITIONS)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_event_payload(
    *,
    lesson_id: int,
    student_id: int | None,
    event_type: str,
    source: str,
    payload: dict | None,
) -> dict:
    payload = dict(payload or {})
    confidence = payload.get("confidence")
    status = payload.get("status") or payload.get("attendance_status") or "observed"

    return {
        "schema": SCHEMA_VERSION,
        "event_type": event_type,
        "lesson_id": lesson_id,
        "user_id": student_id,
        "student_id": student_id,
        "timestamp": payload.get("timestamp") or utc_now_iso(),
        "source": source,
        "status": status,
        "confidence": confidence,
        "manual_review_required": bool(payload.get("manual_review_required", False)),
        "data": payload,
    }
