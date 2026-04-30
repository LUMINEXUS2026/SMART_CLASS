from app.extensions import db


class TeacherGroupLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    group_id = db.Column(db.Integer, db.ForeignKey("group.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    teacher = db.relationship("User", backref="teacher_group_links")
    group = db.relationship("Group", backref="teacher_links")

    __table_args__ = (
        db.UniqueConstraint("teacher_id", "group_id", name="uq_teacher_group"),
    )

