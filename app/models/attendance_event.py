from app.extensions import db


class AttendanceEvent(db.Model):
    __tablename__ = "attendance_events"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, server_default=db.func.now(), nullable=False, index=True)
    status = db.Column(db.String(40), nullable=False, index=True)
    source = db.Column(db.String(40), nullable=False, index=True)
    confirmed_by_teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    user = db.relationship("User", foreign_keys=[user_id], backref="attendance_events")
    lesson = db.relationship("Lesson", backref="attendance_events")
    confirmed_by_teacher = db.relationship("User", foreign_keys=[confirmed_by_teacher_id])
