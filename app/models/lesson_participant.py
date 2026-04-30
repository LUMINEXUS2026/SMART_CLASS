from app.extensions import db


class LessonParticipant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    joined_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    left_at = db.Column(db.DateTime)
    is_present_by_camera = db.Column(db.Boolean, default=False, nullable=False)

    lesson = db.relationship("Lesson", backref="participants")
    student = db.relationship("User", backref="lesson_participations")

    __table_args__ = (
        db.UniqueConstraint("lesson_id", "student_id", name="uq_lesson_student"),
    )

