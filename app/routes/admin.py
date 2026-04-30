from flask import Blueprint, render_template

from app.models import Lesson, User
from app.routes.guards import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/dashboard")
@roles_required("admin")
def dashboard():
    users = User.query.order_by(User.created_at.desc()).limit(50).all()
    lessons = Lesson.query.order_by(Lesson.starts_at.desc()).limit(20).all()
    return render_template("admin/dashboard.html", users=users, lessons=lessons)

