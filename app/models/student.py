from app.extensions import db


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, unique=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False, index=True)
    full_name = db.Column(db.String(160), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    user = db.relationship("User", backref=db.backref("student_profile", uselist=False))
    group = db.relationship("Group", backref="students")

