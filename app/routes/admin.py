from collections import Counter, defaultdict

from flask import Blueprint, render_template

from app.models import (
    Group,
    Lesson,
    LessonEvent,
    PolicySettings,
    Student,
    TeacherGroupLink,
    User,
)
from app.routes.guards import roles_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.get("/dashboard")
@roles_required("admin")
def dashboard():
    users = User.query.order_by(User.created_at.desc()).all()
    teachers = [user for user in users if user.role == "teacher"]
    parents = [user for user in users if user.role == "parent"]
    students = Student.query.order_by(Student.full_name.asc()).all()
    groups = Group.query.order_by(Group.name.asc()).all()
    lessons = Lesson.query.order_by(Lesson.starts_at.desc()).limit(30).all()
    policy = PolicySettings.query.filter_by(name="default").first()

    group_stats = []
    for group in groups:
        group_lessons = Lesson.query.filter_by(group_id=group.id).all()
        lesson_ids = [lesson.id for lesson in group_lessons]
        events = LessonEvent.query.filter(LessonEvent.lesson_id.in_(lesson_ids)).all() if lesson_ids else []
        counts = Counter(event.event_type for event in events)
        group_stats.append(
            {
                "group": group,
                "lessons": len(group_lessons),
                "students": len(group.students),
                "arrived": counts["student_arrived"],
                "late": counts["student_late"],
                "left": counts["student_left_during_lesson"],
                "distractions": counts["distraction_detected"],
                "difficulty": counts["difficulty_indicator_detected"],
            }
        )

    return render_template(
        "admin/dashboard.html",
        users=users,
        teachers=teachers,
        parents=parents,
        students=students,
        groups=groups,
        lessons=lessons,
        group_stats=group_stats,
        policy=policy,
        teacher_links=TeacherGroupLink.query.all(),
    )
