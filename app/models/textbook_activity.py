from app.extensions import db


class TextbookActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    page_index = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(60), nullable=False)
    duration_sec = db.Column(db.Integer, default=0, nullable=False)
    payload_json = db.Column(db.Text, default="{}", nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    lesson = db.relationship("Lesson", backref="textbook_activity")
    student = db.relationship("User")

