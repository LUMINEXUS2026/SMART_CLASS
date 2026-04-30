import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'instance' / 'smart_class.sqlite'}",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TEXTBOOK_DIR = BASE_DIR / "content" / "math6"
    CAMERA_EVENT_TOKEN = os.getenv("CAMERA_EVENT_TOKEN", "dev-camera-token")

