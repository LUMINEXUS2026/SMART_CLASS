from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db
from app.models import User
from app.services.attendance_service import active_lesson_for_student, record_student_login_presence, record_student_logout

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

ALLOWED_ROLES = {"parent", "teacher", "admin"}


@auth_bp.get("/login")
def login():
    if current_user.is_authenticated:
        return redirect_after_login()
    return render_template("auth/login.html")


@auth_bp.post("/login")
def login_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        flash("Неверный логин или пароль.")
        return redirect(url_for("auth.login"))
    if user.role == "student" and not active_lesson_for_student(user):
        flash("Сейчас нет активного урока для этого ученика.")
        return redirect(url_for("auth.login"))

    login_user(user)
    if user.role == "student":
        participant = record_student_login_presence(user)
        db.session.commit()
        return redirect(url_for("student.lesson", lesson_id=participant.lesson_id))
    return redirect_after_login()


@auth_bp.get("/register")
def register():
    return render_template("auth/register.html", roles=sorted(ALLOWED_ROLES))


@auth_bp.post("/register")
def register_post():
    email = request.form.get("email", "").strip().lower()
    name = request.form.get("name", "").strip()
    role = request.form.get("role", "student")
    password = request.form.get("password", "")

    if role not in ALLOWED_ROLES:
        flash("Неизвестная роль.")
        return redirect(url_for("auth.register"))
    if not email or not name or len(password) < 6:
        flash("Заполните имя, почту и пароль от 6 символов.")
        return redirect(url_for("auth.register"))
    if User.query.filter_by(email=email).first():
        flash("Пользователь с такой почтой уже есть.")
        return redirect(url_for("auth.register"))

    user = User(
        email=email,
        name=name,
        role=role,
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    login_user(user)
    return redirect_after_login()


@auth_bp.post("/logout")
def logout():
    if current_user.is_authenticated and current_user.role == "student":
        record_student_logout(current_user)
        db.session.commit()
    logout_user()
    return redirect(url_for("auth.login"))


def redirect_after_login():
    if current_user.role == "teacher":
        return redirect(url_for("teacher.dashboard"))
    if current_user.role == "admin":
        return redirect(url_for("admin.dashboard"))
    if current_user.role == "parent":
        return redirect(url_for("parent.dashboard"))
    if current_user.role == "student":
        return redirect(url_for("student.dashboard"))
    return redirect(url_for("auth.login"))
