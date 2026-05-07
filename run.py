from datetime import datetime, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import (
    Classroom,
    CourseEnrollment,
    CourseSchedule,
    Group,
    Lesson,
    LessonEvent,
    LessonParticipant,
    LessonSummary,
    Notification,
    ParentStudentLink,
    PolicySettings,
    Student,
    TeacherGroupLink,
    TextbookActivity,
    User,
)

app = create_app()


@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")


@app.cli.command("seed-demo")
def seed_demo():
    seed_role_demo()


@app.cli.command("import-real-schedule")
def import_real_schedule_command():
    from pathlib import Path

    from app.services.schedule_import import import_real_schedule

    downloads = Path.home() / "Downloads"
    files = []
    for file_path in downloads.glob("*.xlsx"):
        escaped_name = file_path.name.encode("unicode_escape").decode("ascii")
        if "\\u0420\\u0435\\u0433\\u0438" in escaped_name and "\\u041e\\u0442\\u0432" in escaped_name:
            files.append(file_path)

    if not files:
        raise SystemExit("Schedule workbook was not found in Downloads.")

    summary = import_real_schedule(max(files, key=lambda item: item.stat().st_mtime))
    print("Real schedule imported.")
    print(f"Teachers: {len(summary.teacher_accounts)}")
    print(f"Students: {summary.students}")
    print(f"Schedule slots: {summary.schedules}")
    print(f"Enrollments: {summary.enrollments}")
    print("Teacher accounts:")
    for name, email in summary.teacher_accounts.items():
        print(f"- {name}: {email} / password")


@app.cli.command("seed-role-demo")
def seed_role_demo():
    db.drop_all()
    db.create_all()

    admin = make_user("admin@example.com", "Администратор EDUCAM", "admin")
    teachers = [
        make_user("teacher1@example.com", "Иванова Е.В.", "teacher"),
        make_user("teacher2@example.com", "Петров А.И.", "teacher"),
        make_user("teacher3@example.com", "Козлова Н.А.", "teacher"),
    ]
    parents = [
        make_user(f"parent{i}@example.com", f"Родитель {i}", "parent")
        for i in range(1, 11)
    ]
    student_users = [
        make_user(f"student{i}@example.com", name, "student")
        for i, name in enumerate(
            [
                "Абрамова А.",
                "Белов Д.",
                "Васильева К.",
                "Григорьев М.",
                "Дмитриева С.",
                "Егоров П.",
                "Жукова Е.",
                "Зайцев И.",
                "Ильина М.",
                "Кузнецов Р.",
            ],
            start=1,
        )
    ]
    db.session.add_all([admin, *teachers, *parents, *student_users])
    db.session.flush()

    groups = [
        Group(name="6А · Математика", description="Основная пилотная группа"),
        Group(name="6Б · Физика", description="Вторая учебная группа"),
        Group(name="6В · Информатика", description="Группа для цифрового учебника"),
    ]
    db.session.add_all(groups)
    db.session.flush()

    students = []
    for index, user in enumerate(student_users):
        student = Student(user_id=user.id, group_id=groups[index % len(groups)].id, full_name=user.name)
        students.append(student)
        db.session.add(student)
    db.session.flush()

    for parent, student in zip(parents, students):
        db.session.add(ParentStudentLink(parent_id=parent.id, student_id=student.id))

    db.session.add_all(
        [
            TeacherGroupLink(teacher_id=teachers[0].id, group_id=groups[0].id),
            TeacherGroupLink(teacher_id=teachers[1].id, group_id=groups[1].id),
            TeacherGroupLink(teacher_id=teachers[2].id, group_id=groups[2].id),
        ]
    )

    now = datetime.now()
    lessons = [
        Lesson(title="Квадратные уравнения. Формула дискриминанта", subject="Математика", status="active", teacher_id=teachers[0].id, group_id=groups[0].id, starts_at=now - timedelta(minutes=20)),
        Lesson(title="Закон Ома для участка цепи", subject="Физика", status="finished", teacher_id=teachers[1].id, group_id=groups[1].id, starts_at=now - timedelta(days=1), ends_at=now - timedelta(days=1, minutes=-45)),
        Lesson(title="Циклы в Python", subject="Информатика", status="finished", teacher_id=teachers[2].id, group_id=groups[2].id, starts_at=now - timedelta(days=2), ends_at=now - timedelta(days=2, minutes=-45)),
    ]
    db.session.add_all(lessons)
    db.session.flush()

    for lesson in lessons:
        for student in Student.query.filter_by(group_id=lesson.group_id).all():
            status = "arrived"
            if student.id % 4 == 0:
                status = "late"
            db.session.add(
                LessonParticipant(
                    lesson_id=lesson.id,
                    student_id=student.user_id,
                    attendance_status=status,
                    is_present_by_camera=status != "absent",
                )
            )
            db.session.add(
                TextbookActivity(
                    lesson_id=lesson.id,
                    student_id=student.user_id,
                    page_index=student.id % 5,
                    action="page_opened",
                    duration_sec=120 + student.id * 10,
                )
            )

    event_plan = [
        (lessons[0], students[0], "student_arrived", "web"),
        (lessons[0], students[3], "student_late", "camera"),
        (lessons[0], students[0], "student_left_during_lesson", "web"),
        (lessons[0], students[0], "student_returned_during_lesson", "web"),
        (lessons[0], students[6], "distraction_detected", "camera"),
        (lessons[0], students[9], "difficulty_indicator_detected", "web"),
        (lessons[1], students[1], "student_left_early", "teacher"),
        (lessons[2], students[2], "difficulty_indicator_detected", "web"),
    ]
    for lesson, student, event_type, source in event_plan:
        db.session.add(
            LessonEvent(
                lesson_id=lesson.id,
                student_id=student.user_id,
                event_type=event_type,
                source=source,
                payload_json="{}",
            )
        )

    for lesson in lessons:
        db.session.add(
            LessonSummary(
                lesson_id=lesson.id,
                summary_text="Краткое summary: урок прошёл штатно, зафиксированы только наблюдаемые события.",
                attendance_count=len(lesson.participants),
                late_count=1,
                exit_count=1 if lesson.id == lessons[0].id else 0,
                distraction_count=1 if lesson.id == lessons[0].id else 0,
                difficulty_count=1,
            )
        )

    first_parent = parents[0]
    first_student = students[0]
    db.session.add_all(
        [
            Notification(user_id=first_parent.id, student_id=first_student.id, lesson_id=lessons[0].id, title="Ребёнок вернулся в урок", message="Зафиксирован возврат в динамический учебник.", level="info"),
            Notification(user_id=first_parent.id, student_id=first_student.id, lesson_id=lessons[0].id, title="Был выход из вкладки", message="Событие требует только внимания, без автоматических выводов.", level="warning"),
        ]
    )

    db.session.add(PolicySettings(name="default", late_after_minutes=10, left_after_minutes=5))
    db.session.commit()
    print("Role demo database seeded.")
    print("admin@example.com / password")
    print("teacher1@example.com / password")
    print("parent1@example.com / password")


def make_user(email, name, role):
    return User(
        email=email,
        name=name,
        role=role,
        password_hash=generate_password_hash("password"),
    )


if __name__ == "__main__":
    app.run(debug=True)
