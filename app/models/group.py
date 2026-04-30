from app.extensions import db


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    description = db.Column(db.String(255), default="", nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

