# SMART_CLASS MVP-1 EDUCAM

SMART_CLASS combines a dynamic textbook, lesson management, observable lesson events, and a separate OpenCV camera worker.

The MVP intentionally records only observable events. It does not perform emotion recognition, psychological conclusions, or automatic punishments.

## Local run

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

## MVP modules

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

