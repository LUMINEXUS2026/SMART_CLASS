# EduCam Camera Service

This folder is for the OpenCV/YOLO worker. It stays separate from the web app and sends
only neutral observable events to EduCam backend.

The worker can detect:

- people with YOLO `person`;
- phones with YOLO `cell phone`;
- known students from `faces_db/<student name>/*.jpg` via OpenCV LBPH.

It sends:

- `student_arrived` when a known face or person is detected;
- `distraction_detected` when a phone is detected.

Do not send emotion labels, psychological conclusions, or punishment decisions.

## Prepare

```powershell
cd "C:\Users\User\Documents\New project 2"
.\.venv\Scripts\python.exe -m pip install -r camera_service\requirements-camera.txt
```

For face recognition, create:

```text
faces_db/
  Абрамова А/
    1.jpg
    2.jpg
  Белов Д/
    1.jpg
```

## Example

```powershell
python camera_service/camera_worker.py `
  --backend http://127.0.0.1:5000 `
  --lesson-id 1 `
  --token dev-camera-token `
  --source 0 `
  --faces-dir faces_db `
  --display
```

RTSP example:

```powershell
python camera_service/camera_worker.py `
  --backend http://127.0.0.1:5000 `
  --lesson-id 1 `
  --token dev-camera-token `
  --source "rtsp://user:password@192.168.1.20:554/stream1" `
  --camera-name "Кабинет 301-А" `
  --faces-dir faces_db
```
