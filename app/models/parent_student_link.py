from app.extensions import db


class ParentStudentLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parent_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    parent = db.relationship("User", backref="parent_links")
    student = db.relationship("Student", backref="parent_links")

    __table_args__ = (
        db.UniqueConstraint("parent_id", "student_id", name="uq_parent_student"),
    )

