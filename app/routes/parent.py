from collections import Counter, defaultdict

from flask import Blueprint, render_template
from flask_login import current_user

from app.models import (
    LessonEvent,
    LessonParticipant,
    Notification,
    ParentStudentLink,
    TextbookActivity,
)
from app.routes.guards import roles_required
from app.services.dashboard_data import discipline_events, parent_child_snapshot

parent_bp = Blueprint("parent", __name__, url_prefix="/parent")

PARENT_VISIBLE_EVENTS = {
    "student_arrived": "пришел",
    "student_late": "опоздал",
    "student_left_during_lesson": "вышел во время урока",
    "student_returned_during_lesson": "вернулся",
    "student_left_early": "ушел раньше",
    "distraction_detected": "отвлечение",
    "difficulty_indicator_detected": "учебное затруднение",
}


@parent_bp.get("/dashboard")
@roles_required("parent")
def dashboard():
    links = ParentStudentLink.query.filter_by(parent_id=current_user.id).all()
    children = [link.student for link in links]
    child_cards = []

    for child in children:
        events = (
            LessonEvent.query.filter_by(student_id=child.user_id)
            .order_by(LessonEvent.created_at.desc())
            .limit(40)
            .all()
        )
        visible_events = [event for event in events if event.event_type in PARENT_VISIBLE_EVENTS]
        latest_status = PARENT_VISIBLE_EVENTS.get(visible_events[0].event_type, "нет активных событий") if visible_events else "нет активных событий"
        counts = Counter(event.event_type for event in visible_events)
        activity_count = TextbookActivity.query.filter_by(student_id=child.user_id).count()
        notifications = (
            Notification.query.filter_by(user_id=current_user.id, student_id=child.id)
            .order_by(Notification.created_at.desc())
            .limit(6)
            .all()
        )
        participations = LessonParticipant.query.filter_by(student_id=child.user_id).all()
        child_cards.append(
            {
                "student": child,
                "latest_status": latest_status,
                "events": visible_events[:8],
                "counts": counts,
                "activity_count": activity_count,
                "notifications": notifications,
                "participations": participations,
            }
        )

    return render_template(
        "parent/dashboard.html",
        child_cards=child_cards,
        labels=PARENT_VISIBLE_EVENTS,
        child_snapshot=parent_child_snapshot(),
        discipline_events=discipline_events(),
    )
