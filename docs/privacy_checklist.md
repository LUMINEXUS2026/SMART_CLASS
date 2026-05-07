# Smart Class MVP privacy checklist

Period: 6-13 May 2026.

Owner: Елизавета.

## Data allowed in MVP

- Internal `user_id`, `student_id`, `lesson_id`, `group_id`.
- Lesson timestamps: login, logout, detected, inactive, warning, manual correction.
- Attendance status: `arrived`, `late`, `absent`, `left`, `returned`, `left_early`.
- AI confidence as a number from `0.0` to `1.0`.
- Neutral camera metadata: camera name, room, frame timestamp, object label.
- Textbook activity metadata: page index, action type, duration.

## Data not allowed in MVP

- Emotion labels, psychological state, personality conclusions.
- Automatic punishments or disciplinary conclusions without teacher review.
- Medical, biometric, passport, address or family-sensitive data.
- Raw video uploads to the web app database.
- Public demo data that identifies real children.

## Anonymization rules

- Demo must use synthetic or consented names.
- Event payloads should use IDs first; names are only display labels.
- Camera worker sends recognition result and confidence, not face embeddings.
- Uncertain AI results must use `manual_review_required: true`.

## Access rules

- Student sees only own lesson module state.
- Parent sees only linked child summary.
- Teacher sees own lessons, attendance correction and review queue.
- Administrator sees full MVP analytics and camera state.

## Video handling

- Video stays local to the camera worker or demo static file.
- Backend receives only observable event JSON.
- If storage is later needed, retention and access must be approved before implementation.

## Reserve scenarios

- Low AI confidence: create `warning` or `detected` with `manual_review_required: true`.
- Camera offline: keep last known state, do not mark student absent automatically.
- Teacher blocks student: do not create exit event until the student is missing after the configured threshold and was near an exit zone.
- Recognition failed: mark the case for teacher review, do not guess identity.
