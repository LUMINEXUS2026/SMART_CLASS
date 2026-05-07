from __future__ import annotations

import json
from collections import Counter

from app.models import TextbookActivity

ACTIVE_ACTIONS = {
    "page_opened",
    "page_changed",
    "task_started",
    "task_completed",
    "answer_checked",
    "help_requested",
}

INACTIVE_ACTIONS = {
    "tab_hidden",
    "pause",
    "long_idle",
    "stalled",
}


def student_activity_score(lesson_id: int, student_id: int) -> dict:
    rows = TextbookActivity.query.filter_by(lesson_id=lesson_id, student_id=student_id).all()
    if not rows:
        return {
            "score": 0,
            "active_actions": 0,
            "inactive_actions": 0,
            "active_seconds": 0,
            "idle_seconds": 0,
            "signals": [],
        }

    counts = Counter(row.action for row in rows)
    active_actions = sum(counts[action] for action in ACTIVE_ACTIONS)
    inactive_actions = sum(counts[action] for action in INACTIVE_ACTIONS)
    active_seconds = sum(row.duration_sec for row in rows if row.action in ACTIVE_ACTIONS)
    idle_seconds = sum(row.duration_sec for row in rows if row.action in INACTIVE_ACTIONS)
    raw = 55 + active_actions * 6 + min(active_seconds // 60, 20) - inactive_actions * 8 - min(idle_seconds // 30, 22)
    score = max(0, min(100, int(raw)))

    signals = []
    if counts["long_idle"] or idle_seconds >= 120:
        signals.append("long_idle")
    if counts["stalled"]:
        signals.append("stalled_on_task")
    if active_actions >= 5:
        signals.append("steady_activity")

    return {
        "score": score,
        "active_actions": active_actions,
        "inactive_actions": inactive_actions,
        "active_seconds": active_seconds,
        "idle_seconds": idle_seconds,
        "signals": signals,
    }


def payload_from_activity(row: TextbookActivity) -> dict:
    try:
        payload = json.loads(row.payload_json or "{}")
    except json.JSONDecodeError:
        payload = {}
    return payload
