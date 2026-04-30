# Camera Service

This folder is for the OpenCV worker. It should stay separate from the web app.

The worker must send only observable events to the backend:

- `student_arrived`
- `student_late`
- `student_left_during_lesson`
- `student_returned_during_lesson`
- `student_left_early`
- `distraction_detected`

Do not send emotion labels, psychological conclusions, or punishment decisions.

## Example

```powershell
python camera_service/camera_worker.py --backend http://127.0.0.1:5000 --lesson-id 1 --token change-camera-token
```

