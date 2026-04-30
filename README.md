# SMART_CLASS MVP-1 EDUCAM

SMART_CLASS is an MVP for EDUCAM: a smart classroom platform with lesson management, a dynamic textbook, camera events, and lesson analytics.

The MVP records only observable events. It does not perform emotion recognition, psychological conclusions, or automatic punishments. The system helps the teacher make decisions.

## Local Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
flask --app run.py init-db
flask --app run.py seed-demo
flask --app run.py run --debug
```

Demo users after `seed-demo`:

- `teacher@example.com` / `password`
- `student@example.com` / `password`
- `parent@example.com` / `password`
- `admin@example.com` / `password`

## MVP Modules

- Registration and login.
- Roles: student, teacher, parent, administrator.
- Teacher creates and finishes a lesson.
- Student joins an active lesson.
- Student is redirected out after teacher finishes the lesson.
- Dynamic textbook pages from `content/math6`.
- Textbook activity tracking.
- Browser tab leave/return tracking.
- Lesson events API.
- Teacher dashboard and lesson report.
- Camera worker stub that sends observable events to the backend.

## Lesson Events

- `student_arrived`
- `student_late`
- `student_left_during_lesson`
- `student_returned_during_lesson`
- `student_left_early`
- `distraction_detected`
- `difficulty_indicator_detected`
- `lesson_summary_ready`

## Camera Service

OpenCV code belongs in `camera_service/`. The web app must not depend directly on camera windows, RTSP streams, or local face folders.

Run the stub:

```powershell
python camera_service/camera_worker.py --backend http://127.0.0.1:5000 --lesson-id 1 --token change-camera-token --dry-run
```

