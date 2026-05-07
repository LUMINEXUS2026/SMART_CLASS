from app.extensions import db


class CourseEnrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("course_schedule.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    status = db.Column(db.String(40), default="active", nullable=False)
    source_row = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    schedule = db.relationship("CourseSchedule", backref="enrollments")
    student = db.relationship("User", backref="course_enrollments")

    __table_args__ = (
        db.UniqueConstraint("schedule_id", "student_id", name="uq_course_enrollment_student"),
    )

