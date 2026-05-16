import json
from collections import Counter
from pathlib import Path

from flask import Blueprint, current_app, flash, jsonify, redirect, render_template, request, send_file, url_for

from app.models import (
    Classroom,
    CourseEnrollment,
    CourseSchedule,
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

DEFAULT_CLASSROOM_5_RTSP = "rtsp://admin:password@192.168.0.106:554/h264_stream"


def classroom_5_config_path() -> Path:
    return Path(current_app.instance_path) / "camera_config" / "classroom_5.json"


def classroom_5_snapshot_path() -> Path:
    return Path(current_app.instance_path) / "camera_state" / "classroom_5.jpg"


def load_classroom_5_config() -> dict:
    config = {
        "source_type": "ip_camera",
        "source": DEFAULT_CLASSROOM_5_RTSP,
    }
    path = classroom_5_config_path()
    if path.exists():
        try:
            config.update(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            pass
    return config


def save_classroom_5_config(config: dict) -> None:
    path = classroom_5_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


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


@admin_bp.get("/schedule")
@roles_required("admin")
def schedule():
    schedules = (
        CourseSchedule.query
        .join(CourseSchedule.teacher)
        .join(CourseSchedule.classroom)
        .order_by(Classroom.number.asc(), User.name.asc(), CourseSchedule.day_of_week.asc(), CourseSchedule.starts_at.asc())
        .all()
    )
    students = User.query.filter_by(role="student").order_by(User.name.asc()).all()
    enrollments = CourseEnrollment.query.all()
    return render_template(
        "admin/schedule.html",
        schedules=schedules,
        students=students,
        enrollments=enrollments,
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
    return render_template("admin/settings.html", policy=policy, teachers=teachers, groups=groups, cameras=classroom_camera_feeds())


@admin_bp.get("/cameras")
@roles_required("admin")
def cameras():
    return render_template("admin/cameras.html", cameras=classroom_camera_feeds(), discipline_events=discipline_events())


@admin_bp.post("/cameras/classroom-5/source")
@roles_required("admin")
def update_classroom_5_camera_source():
    source_type = request.form.get("source_type", "ip_camera")
    if source_type not in {"ip_camera", "demo_video"}:
        source_type = "ip_camera"

    source = request.form.get("source", "").strip()
    if not source:
        source = DEFAULT_CLASSROOM_5_RTSP if source_type == "ip_camera" else "app/static/videos/english_class_demo.mp4"

    save_classroom_5_config({"source_type": source_type, "source": source})
    flash("Источник камеры обновлен.", "success")
    return redirect(url_for("admin.classroom_5_camera"))


@admin_bp.get("/cameras/classroom-5")
@roles_required("admin")
def classroom_5_camera():
    camera = next(camera for camera in camera_feeds() if camera.display_mode == "ip_camera")
    return render_camera_detail(camera, load_classroom_5_config())


@admin_bp.get("/cameras/classroom-5/demo")
@roles_required("admin")
def classroom_5_demo_camera():
    camera = next(camera for camera in camera_feeds() if camera.display_mode == "demo_video")
    return render_camera_detail(
        camera,
        {
            "source_type": "demo_video",
            "source": "app/static/videos/english_class_demo.mp4",
        },
    )


def render_camera_detail(camera, camera_config):
    return render_template(
        "admin/camera_detail.html",
        camera=camera,
        camera_config=camera_config,
        discipline_events=discipline_events(),
        analysis=lesson_analysis_data(),
    )


def classroom_camera_feeds():
    config = load_classroom_5_config()
    source_type = config.get("source_type", "ip_camera")
    feeds = camera_feeds()
    classroom_feed = next((camera for camera in feeds if camera.display_mode == source_type), None)
    closed_feeds = [camera for camera in feeds if camera.display_mode == "closed"]
    return ([classroom_feed] if classroom_feed else []) + closed_feeds


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


@admin_bp.get("/cameras/classroom-5/snapshot")
@roles_required("admin")
def classroom_5_camera_snapshot():
    snapshot_path = classroom_5_snapshot_path()
    if snapshot_path.exists():
        return send_file(snapshot_path, mimetype="image/jpeg", max_age=0)
    return "", 404
