from app.extensions import db


class LessonTextbookState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey("lesson.id"), nullable=False, unique=True, index=True)
    assigned_page_index = db.Column(db.Integer, default=0, nullable=False)
    assigned_title = db.Column(db.String(200), default="", nullable=False)
    study_mode = db.Column(db.String(24), default="textbook", nullable=False)
    updated_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    lesson = db.relationship("Lesson", backref=db.backref("textbook_state", uselist=False))
    updated_by = db.relationship("User")
