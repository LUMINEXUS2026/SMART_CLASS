import unittest
import json
from datetime import datetime

from werkzeug.security import generate_password_hash

from app import create_app
from app.extensions import db
from app.models import Group, Lesson, LessonEvent, LessonParticipant, Student, User


class TestConfig:
    SECRET_KEY = "test"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    CAMERA_EVENT_TOKEN = "test-camera-token"
    TEXTBOOK_DIR = None


class MvpChainTest(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        db.create_all()
        self.seed_minimal_lesson()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def seed_minimal_lesson(self):
        teacher = User(
            email="teacher@example.com",
            name="Teacher",
            role="teacher",
            password_hash=generate_password_hash("password"),
        )
        student_user = User(
            email="student@example.com",
            name="Student",
            role="student",
            password_hash=generate_password_hash("password"),
        )
        group = Group(name="Group 1")
        db.session.add_all([teacher, student_user, group])
        db.session.flush()

        db.session.add(Student(user_id=student_user.id, group_id=group.id, full_name="Student"))
        lesson = Lesson(
            title="English",
            subject="English",
            status="active",
            teacher_id=teacher.id,
            group_id=group.id,
            starts_at=datetime.now(),
        )
        db.session.add(lesson)
        db.session.commit()

    def test_student_login_creates_attendance_event(self):
        response = self.client.post(
            "/auth/login",
            data={"email": "student@example.com", "password": "password"},
            follow_redirects=False,
        )

        self.assertEqual(response.status_code, 302)
        student = User.query.filter_by(email="student@example.com").one()
        lesson = Lesson.query.filter_by(title="English").one()
        participant = LessonParticipant.query.filter_by(lesson_id=lesson.id, student_id=student.id).one()
        event_types = [event.event_type for event in LessonEvent.query.order_by(LessonEvent.id.asc()).all()]

        self.assertEqual(participant.attendance_status, "arrived")
        self.assertIn("login", event_types)
        self.assertIn("student_arrived", event_types)

    def test_ai_low_confidence_detection_requires_review(self):
        student = User.query.filter_by(email="student@example.com").one()
        lesson = Lesson.query.filter_by(title="English").one()

        response = self.client.post(
            "/api/ai/detections",
            headers={"X-Camera-Token": "test-camera-token"},
            json={
                "lesson_id": lesson.id,
                "user_id": student.id,
                "detected": True,
                "confidence": 0.42,
                "timestamp": "2026-05-07T10:30:00Z",
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data["manual_review_required"])

        detected = LessonEvent.query.filter_by(event_type="detected").one()
        warning = LessonEvent.query.filter_by(event_type="warning").one()
        self.assertEqual(detected.review_status, "pending")
        self.assertEqual(warning.review_status, "pending")

    def test_camera_confidence_boundary_on_both_api_paths(self):
        student = User.query.filter_by(email="student@example.com").one()
        lesson = Lesson.query.filter_by(title="English").one()
        for confidence, expected_status in [(0.749, "pending"), (0.75, "confirmed"), (0.751, "confirmed")]:
            with self.subTest(confidence=confidence):
                ai_response = self.client.post(
                    "/api/ai/detections",
                    headers={"X-Camera-Token": "test-camera-token"},
                    json={"lesson_id": lesson.id, "user_id": student.id, "detected": True,
                          "confidence": confidence},
                )
                self.assertEqual(ai_response.status_code, 200)
                ai_event = db.session.get(LessonEvent, ai_response.get_json()["event_id"])
                camera_response = self.client.post(
                    "/api/camera/events",
                    headers={"X-Camera-Token": "test-camera-token"},
                    json={"lesson_id": lesson.id, "student_name": student.name,
                          "event_type": "student_arrived", "payload": {"confidence": confidence,
                          "manual_review_required": False}},
                )
                self.assertEqual(camera_response.status_code, 200)
                camera_event = db.session.get(LessonEvent, camera_response.get_json()["event_id"])
                for event in (ai_event, camera_event):
                    self.assertEqual(event.review_status, expected_status)
                    self.assertEqual(json.loads(event.payload_json)["manual_review_required"],
                                     expected_status == "pending")

        missing_response = self.client.post(
            "/api/camera/events", headers={"X-Camera-Token": "test-camera-token"},
            json={"lesson_id": lesson.id, "student_name": student.name, "event_type": "student_arrived"},
        )
        missing_event = db.session.get(LessonEvent, missing_response.get_json()["event_id"])
        self.assertEqual(missing_event.review_status, "pending")

    def test_textbook_activity_creates_unified_event(self):
        self.client.post(
            "/auth/login",
            data={"email": "student@example.com", "password": "password"},
            follow_redirects=False,
        )
        lesson = Lesson.query.filter_by(title="English").one()

        response = self.client.post(
            f"/api/lessons/{lesson.id}/textbook-activity",
            json={"action": "long_idle", "page_index": 0, "duration_sec": 190},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(LessonEvent.query.filter_by(event_type="textbook_action").count(), 1)
        inactive = LessonEvent.query.filter_by(event_type="inactive").one()
        self.assertEqual(inactive.review_status, "pending")


if __name__ == "__main__":
    unittest.main()
