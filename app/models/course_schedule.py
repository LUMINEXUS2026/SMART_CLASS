from app.extensions import db


class CourseSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False, index=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), nullable=False, index=True)
    title = db.Column(db.String(180), nullable=False)
    subject = db.Column(db.String(120), nullable=False)
    direction = db.Column(db.String(120), default="", nullable=False)
    day_of_week = db.Column(db.String(32), nullable=False, index=True)
    starts_at = db.Column(db.String(16), nullable=False)
    ends_at = db.Column(db.String(16), nullable=False)
    source = db.Column(db.String(80), default="real_schedule_xlsx", nullable=False)
    source_row = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    teacher = db.relationship("User", backref="course_schedules")
    group = db.relationship("Group", backref="course_schedules")
    classroom = db.relationship("Classroom", backref="course_schedules")

    __table_args__ = (
        db.UniqueConstraint(
            "teacher_id",
            "group_id",
            "classroom_id",
            "day_of_week",
            "starts_at",
            "ends_at",
            name="uq_course_schedule_slot",
        ),
    )

