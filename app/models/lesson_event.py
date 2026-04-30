from app.extensions import db


class LessonEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), index=True)
    event_type = db.Column(db.String(80), nullable=False, index=True)
    source = db.Column(db.String(40), default="web", nullable=False)
    payload_json = db.Column(db.Text, default="{}", nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False, index=True)

    lesson = db.relationship("Lesson", backref="events")
    student = db.relationship("User")

