# Smart Class MVP event dictionary

Owner: Жабин Роман.

The MVP uses one event envelope for auth, attendance, textbook and AI data.

## Minimal MVP events

| Event | Meaning | Source | Review |
| --- | --- | --- | --- |
| `login` | User entered the system or active lesson module | auth | auto |
| `logout` | User left the system | auth | auto |
| `detected` | AI detected a known user or person | ai/camera | manual if low confidence |
| `absent` | Student is not confirmed present | ai/teacher | manual |
| `inactive` | Long inactivity in the textbook module | textbook | auto/manual if long |
| `warning` | Neutral warning requiring teacher attention | ai/camera/textbook | manual |
| `student_arrived` | Presence confirmed | auth/web/camera | auto |
| `student_late` | Student joined after late threshold | auth/web/teacher | auto |
| `student_left_during_lesson` | Student may have left tab or classroom | web/camera | manual |
| `student_returned_during_lesson` | Student returned | web/camera | auto |
| `student_left_early` | Teacher confirmed early exit | teacher | manual |
| `distraction_detected` | Observable distraction signal, for example phone | camera | manual |
| `difficulty_indicator_detected` | Help request or difficulty signal | textbook | auto |
| `textbook_action` | Page, task, pause and module actions | textbook | auto |
| `attendance_manual_update` | Teacher corrected status | teacher | auto |

## Event envelope

```json
{
  "schema": "smart-class.event.v1",
  "event_type": "detected",
  "lesson_id": 1,
  "user_id": 7,
  "student_id": 7,
  "timestamp": "2026-05-07T10:30:00Z",
  "source": "ai",
  "status": "detected",
  "confidence": 0.82,
  "manual_review_required": false,
  "data": {
    "camera": "Camera 5-A",
    "raw": {}
  }
}
```

## API endpoints

- `GET /api/event-types` returns the canonical dictionary.
- `POST /api/lessons/<lesson_id>/events` creates a web event for an authenticated user.
- `POST /api/lessons/<lesson_id>/textbook-activity` stores textbook activity and creates `textbook_action`.
- `POST /api/camera/events` accepts camera worker events with `X-Camera-Token`.
- `POST /api/ai/detections` accepts AI result: `detected`, `confidence`, `timestamp`, `user_id`, `lesson_id`.
