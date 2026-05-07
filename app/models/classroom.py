from app.extensions import db


class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(20), nullable=False, unique=True, index=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(255), default="", nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

