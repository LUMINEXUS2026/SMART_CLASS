from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CameraFeed:
    name: str
    room: str
    kind: str
    status: str
    resolution: str
    attention: int
    detections: int
    enabled: bool = True
    featured: bool = False


def school_overview():
    return {
        "lesson_score": 83,
        "teacher_engagement": 87,
        "student_attention": 74,
        "recorded_lessons": "4/36",
        "remarks": 3,
        "material_accuracy": 94,
        "plan_following": 88,
        "cameras_online": 7,
        "cameras_offline": 1,
    }


def recent_lessons():
    return [
        {"subject": "Математика", "teacher": "Иванова Е.В.", "topic": "Квадратные уравнения. Формула дискриминанта", "time": "09:00-09:45", "score": 82, "status": "Завершён"},
        {"subject": "Физика", "teacher": "Петров А.И.", "topic": "Закон Ома для участка цепи", "time": "10:00-10:45", "score": 76, "status": "Завершён"},
        {"subject": "Информатика", "teacher": "Сидорова М.П.", "topic": "Циклы в Python. Цикл for и while", "time": "11:00-11:45", "score": 79, "status": "Запись"},
        {"subject": "Русский язык", "teacher": "Козлова Н.А.", "topic": "Сложноподчинённые предложения", "time": "09:00-09:45", "score": 91, "status": "Завершён"},
    ]


def teacher_ratings():
    return [
        {"name": "Козлова Н.А.", "score": 91},
        {"name": "Иванова Е.В.", "score": 87},
        {"name": "Сидорова М.П.", "score": 82},
        {"name": "Петров А.И.", "score": 76},
        {"name": "Морозов Д.С.", "score": 72},
        {"name": "Волков И.Г.", "score": 68},
    ]


def camera_feeds():
    return [
        CameraFeed("Камера 5-А", "Кабинет 5", "класс английского", "В сети", "1920x1080", 86, 14, True, True),
        CameraFeed("Камера 301-А", "Кабинет 301", "фронтальная", "В сети", "1920x1080", 67, 10, True, True),
        CameraFeed("Камера 301-B", "Кабинет 301", "задняя", "В сети", "1920x1080", 75, 5, True, True),
        CameraFeed("Камера 302-А", "Кабинет 302", "широкоугольная", "В сети", "2560x1440", 67, 6, True),
        CameraFeed("Камера 204-А", "Кабинет 204", "фронтальная", "В сети", "1920x1080", 58, 3, True),
        CameraFeed("Камера 204-B", "Кабинет 204", "задняя", "В сети", "1920x1080", 61, 4, True),
        CameraFeed("Камера 105-А", "Кабинет 105", "фронтальная", "В сети", "1920x1080", 69, 7, True),
        CameraFeed("Камера 310-А", "Кабинет 310", "широкоугольная", "В сети", "2560x1440", 74, 6, True),
        CameraFeed("Камера Спортзал", "Спортзал", "широкоугольная", "Откл.", "2560x1440", 0, 0, False),
    ]


def discipline_events():
    return [
        {"level": "info", "tag": "AI распознавание", "title": "Кабинет 5: урок английского", "text": "Учитель Киреева Ирина, распознаны ученики в классе, телефон не подтверждён.", "room": "Кабинет 5", "time": "10:30"},
        {"level": "warning", "tag": "Телефон", "title": "Использование телефона", "text": "Ученик использует телефон во время контрольной работы.", "room": "Кабинет 301", "time": "13:18"},
        {"level": "info", "tag": "Низкая вовлечённость", "title": "Критическое снижение внимания", "text": "Внимание класса: 35%. 8 учеников из 22 отвлечены.", "room": "Кабинет 302", "time": "13:45"},
        {"level": "critical", "tag": "Учитель", "title": "Учитель отсутствует", "text": "Учителя нет в рабочей зоне больше 5 минут.", "room": "Кабинет 302", "time": "11:28"},
        {"level": "warning", "tag": "Нарушение зоны", "title": "Ученик покинул зону", "text": "Ученик вышел из рабочей зоны и подошёл к серверному шкафу.", "room": "Кабинет 204", "time": "14:02"},
        {"level": "warning", "tag": "Шум", "title": "Повышенный уровень шума", "text": "Шум на 6 дБ выше нормы, но в пределах допустимого для практики.", "room": "Кабинет 310", "time": "13:30"},
        {"level": "info", "tag": "Внимание", "title": "Снижение внимания после обеда", "text": "Внимание ниже обычного на 12 пунктов.", "room": "Кабинет 301", "time": "12:08"},
    ]


def lesson_analysis():
    return {
        "title": "Квадратные уравнения. Формула дискриминанта",
        "subject": "Математика",
        "teacher": "Иванова Е.В.",
        "date": "2026-04-30",
        "time": "09:00-09:45",
        "duration": "45 мин",
        "score": 82,
        "protocol_done": "21/28",
        "attendance": "23/25",
        "questions": 7,
        "phones": 4,
        "noise": "62 дБ",
        "audio_position": "07:25",
        "audio_total": "35:30",
        "attendance_rows": [
            {"student": "Абрамова А.", "status": "Здесь", "attention": 88, "phone": "-", "distraction": "2 мин"},
            {"student": "Белов Д.", "status": "Здесь", "attention": 72, "phone": "1x", "distraction": "8 мин"},
            {"student": "Васильева К.", "status": "Здесь", "attention": 95, "phone": "-", "distraction": "1 мин"},
            {"student": "Григорьев М.", "status": "Здесь", "attention": 65, "phone": "-", "distraction": "12 мин"},
            {"student": "Дмитриева С.", "status": "Здесь", "attention": 91, "phone": "-", "distraction": "2 мин"},
            {"student": "Егоров П.", "status": "Нет", "attention": 0, "phone": "-", "distraction": "-"},
        ],
        "speech": {
            "speed": "128 сл/мин",
            "volume": "62 дБ",
            "pauses": "14 шт",
            "filler_words": "7 шт",
            "expressiveness": 74,
            "questions_total": 12,
            "questions_to_students": 7,
            "praise": 5,
        },
        "plan": [
            {"title": "Приветствие класса", "time": "00:00", "status": "done", "note": "Приветствие зафиксировано"},
            {"title": "Объявление темы урока", "time": "00:08", "status": "done", "note": "Тема урока объявлена"},
            {"title": "Озвучивание плана урока", "time": "01:10", "status": "issue", "note": "План урока не был озвучен явно в начале"},
            {"title": "Связь с предыдущей темой", "time": "06:12", "status": "done", "note": "Актуализация знаний выполнена"},
            {"title": "Подведение итогов урока", "time": "30:55", "status": "done", "note": "Учитель перечислил 5 ключевых пунктов"},
            {"title": "Домашнее задание", "time": "32:55", "status": "done", "note": "Домашнее задание озвучено"},
        ],
        "transcript": [
            {"time": "00:00", "speaker": "Учитель", "text": "Доброе утро, ребята. Сегодня мы разберём квадратные уравнения."},
            {"time": "00:42", "speaker": "Учитель", "text": "Откройте динамический учебник на странице с формулой дискриминанта."},
            {"time": "07:25", "speaker": "Ученик", "text": "Если дискриминант отрицательный, корней нет?"},
            {"time": "07:40", "speaker": "Учитель", "text": "Верно. Сейчас закрепим это на примерах."},
        ],
    }


def analytics_series():
    return {
        "attention": [80, 86, 88, 72, 81, 88, 55, 66, 74, 45],
        "engagement": [84, 89, 91, 76, 84, 90, 62, 70, 78, 50],
        "attendance_by_room": [
            {"room": "Математика", "present": 23, "late": 1, "absent": 1},
            {"room": "Физика", "present": 20, "late": 1, "absent": 1},
            {"room": "Информатика", "present": 18, "late": 1, "absent": 1},
            {"room": "Русский язык", "present": 26, "late": 1, "absent": 1},
            {"room": "Химия", "present": 22, "late": 1, "absent": 1},
            {"room": "Физкультура", "present": 27, "late": 1, "absent": 2},
        ],
        "heatmap": [
            [85, 90, 82, 75, 68, 72, 60, 52],
            [80, 88, 85, 78, 70, 65, 58, 48],
            [88, 92, 86, 80, 74, 70, 62, 55],
            [78, 84, 80, 72, 66, 60, 54, 45],
            [75, 82, 78, 70, 62, 55, 48, 40],
        ],
    }


def parent_child_snapshot():
    return {
        "name": "Абрамова А.",
        "group": "6А · Математика",
        "productivity": 84,
        "activity": 91,
        "attendance": 96,
        "discipline": 78,
        "late": 1,
        "violations": 2,
        "teacher_summary": "На уроке работала стабильно, открывала динамический учебник, один раз выходила из вкладки и быстро вернулась.",
        "subjects": [
            {"name": "Математика", "progress": 86, "note": "активно решает задачи"},
            {"name": "Физика", "progress": 72, "note": "нужны повторения"},
            {"name": "Информатика", "progress": 91, "note": "высокая активность"},
        ],
    }
