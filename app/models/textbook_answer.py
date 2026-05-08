from app.extensions import db


class TextbookAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    page_index = db.Column(db.Integer, nullable=False, index=True)
    task_key = db.Column(db.String(80), nullable=False)
    answer_text = db.Column(db.Text, default="", nullable=False)
    is_correct = db.Column(db.Boolean, nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    lesson = db.relationship("Lesson", backref="textbook_answers")
    student = db.relationship("User")

