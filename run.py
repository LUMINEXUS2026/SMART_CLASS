from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()


@app.cli.command("init-db")
def init_db():
    db.create_all()
    print("Database initialized.")


@app.cli.command("seed-demo")
def seed_demo():
    db.create_all()
    demo_users = [
        ("teacher@example.com", "Учитель", "teacher"),
        ("student@example.com", "Ученик", "student"),
        ("parent@example.com", "Родитель", "parent"),
        ("admin@example.com", "Администратор", "admin"),
    ]
    for email, name, role in demo_users:
        if not User.query.filter_by(email=email).first():
            db.session.add(
                User(
                    email=email,
                    name=name,
                    role=role,
                    password_hash=generate_password_hash("password"),
                )
            )
    db.session.commit()
    print("Demo users seeded.")


if __name__ == "__main__":
    app.run(debug=True)

