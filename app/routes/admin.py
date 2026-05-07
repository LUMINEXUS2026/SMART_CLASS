import json
from collections import Counter
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template

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
from app.services.dashboard_data import (
    analytics_series,
    camera_feeds,
    discipline_events,
    lesson_analysis as lesson_analysis_data,
    recent_lessons,
    school_overview,
    teacher_ratings,
)

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
        overview=school_overview(),
        recent_lessons=recent_lessons(),
        teacher_ratings=teacher_ratings(),
        discipline_events=discipline_events(),
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


@admin_bp.get("/lesson-analysis")
@roles_required("admin")
def lesson_analysis():
    lessons = Lesson.query.order_by(Lesson.starts_at.desc()).limit(20).all()
    return render_template("admin/lesson_analysis.html", lessons=lessons, analysis=lesson_analysis_data())


@admin_bp.get("/events")
@roles_required("admin")
def events():
    lesson_events = LessonEvent.query.order_by(LessonEvent.created_at.desc()).limit(80).all()
    counts = Counter(event.event_type for event in lesson_events)
    return render_template("admin/events.html", events=lesson_events, counts=counts, discipline_events=discipline_events())


@admin_bp.get("/analytics")
@roles_required("admin")
def analytics():
    rows = []
    for group in Group.query.order_by(Group.name.asc()).all():
        lessons = Lesson.query.filter_by(group_id=group.id).all()
        lesson_ids = [lesson.id for lesson in lessons]
        group_events = LessonEvent.query.filter(LessonEvent.lesson_id.in_(lesson_ids)).all() if lesson_ids else []
        counts = Counter(event.event_type for event in group_events)
        rows.append(
            {
                "group": group,
                "attendance": counts["student_arrived"],
                "late": counts["student_late"],
                "left": counts["student_left_during_lesson"],
                "distraction": counts["distraction_detected"],
                "difficulty": counts["difficulty_indicator_detected"],
            }
        )
    return render_template("admin/analytics.html", rows=rows, analytics=analytics_series())


@admin_bp.get("/settings")
@roles_required("admin")
def settings():
    policy = PolicySettings.query.filter_by(name="default").first()
    teachers = User.query.filter_by(role="teacher").all()
    groups = Group.query.order_by(Group.name.asc()).all()
    return render_template("admin/settings.html", policy=policy, teachers=teachers, groups=groups, cameras=camera_feeds())


@admin_bp.get("/cameras")
@roles_required("admin")
def cameras():
    return render_template("admin/cameras.html", cameras=camera_feeds(), discipline_events=discipline_events())


@admin_bp.get("/cameras/classroom-5")
@roles_required("admin")
def classroom_5_camera():
    camera = next(camera for camera in camera_feeds() if camera.room == "Кабинет 5")
    return render_template(
        "admin/camera_detail.html",
        camera=camera,
        discipline_events=discipline_events(),
        analysis=lesson_analysis_data(),
    )


@admin_bp.get("/cameras/classroom-5/state")
@roles_required("admin")
def classroom_5_camera_state():
    state_path = Path(current_app.instance_path) / "camera_state" / "classroom_5.json"
    if state_path.exists():
        with state_path.open("r", encoding="utf-8") as state_file:
            return jsonify(json.load(state_file))

    return jsonify(
        {
            "camera": "Камера 5-А",
            "room": "Кабинет 5",
            "lesson": "Английский язык",
            "teacher": "Киреева Ирина",
            "status": "waiting",
            "message": "AI-воркер распознавания еще не запущен",
            "attention": None,
            "people_count": 0,
            "phones_count": 0,
            "frame_width": 0,
            "frame_height": 0,
            "detections": [],
            "recognitions": [],
            "events": [],
        }
    )
