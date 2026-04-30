from app.extensions import db


class PolicySettings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), default="default", nullable=False, unique=True)
    late_after_minutes = db.Column(db.Integer, default=10, nullable=False)
    left_after_minutes = db.Column(db.Integer, default=5, nullable=False)
    notify_parent_on_late = db.Column(db.Boolean, default=True, nullable=False)
    notify_parent_on_left = db.Column(db.Boolean, default=True, nullable=False)
    notify_parent_on_summary = db.Column(db.Boolean, default=True, nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

