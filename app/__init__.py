import os

from flask import Flask

from .config import Config
from .extensions import db, login_manager


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)
    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @app.template_filter("clean_text")
    def clean_text(value, fallback=""):
        text = str(value or "")
        if "???" in text or text.count("?") >= 3:
            return fallback
        if any(marker in text for marker in ("Р", "С", "Ð", "Ñ")):
            for encoding in ("cp1251", "latin1"):
                try:
                    repaired = text.encode(encoding).decode("utf-8")
                except UnicodeError:
                    continue
                if repaired and repaired.count("?") < text.count("?"):
                    return repaired
        return text

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from .routes.auth import auth_bp
    from .routes.events import events_bp
    from .routes.lessons import lessons_bp
    from .routes.parent import parent_bp
    from .routes.admin import admin_bp
    from .routes.ai import ai_bp
    from .routes.demo import demo_bp
    from .routes.reports import reports_bp
    from .routes.student import student_bp
    from .routes.teacher import teacher_bp
    from .routes.textbook import textbook_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(events_bp)
    app.register_blueprint(lessons_bp)
    app.register_blueprint(parent_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(demo_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(textbook_bp)

    @app.get("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))

    return app
