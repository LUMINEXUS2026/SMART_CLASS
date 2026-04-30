from app.extensions import db


class LessonSummary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, unique=True)
    summary_text = db.Column(db.Text, default="", nullable=False)
    attendance_count = db.Column(db.Integer, default=0, nullable=False)
    late_count = db.Column(db.Integer, default=0, nullable=False)
    exit_count = db.Column(db.Integer, default=0, nullable=False)
    distraction_count = db.Column(db.Integer, default=0, nullable=False)
    difficulty_count = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    lesson = db.relationship("Lesson", backref=db.backref("summary", uselist=False))

