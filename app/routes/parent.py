from flask import Blueprint, render_template

from app.models import Lesson
from app.routes.guards import roles_required

parent_bp = Blueprint("parent", __name__, url_prefix="/parent")


@parent_bp.get("/dashboard")
@roles_required("parent")
def dashboard():
    recent_lessons = Lesson.query.order_by(Lesson.starts_at.desc()).limit(10).all()
    return render_template("parent/dashboard.html", recent_lessons=recent_lessons)

