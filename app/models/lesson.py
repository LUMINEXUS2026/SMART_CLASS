from app.extensions import db


class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(120), default="Математика", nullable=False)
    status = db.Column(db.String(20), default="active", nullable=False, index=True)
    starts_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    ends_at = db.Column(db.DateTime)
    late_after_minutes = db.Column(db.Integer, default=10, nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    teacher = db.relationship("User", backref="created_lessons")

