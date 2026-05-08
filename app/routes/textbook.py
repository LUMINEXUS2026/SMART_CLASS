import json
from pathlib import Path
import re

import markdown
from flask import Blueprint, abort, current_app, jsonify, render_template, request, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Lesson, LessonTextbookState, TextbookActivity, TextbookAnswer
from app.routes.guards import roles_required

textbook_bp = Blueprint("textbook", __name__, url_prefix="/textbook")


@textbook_bp.get("/lesson/<int:lesson_id>/page/<int:page_index>")
@roles_required("student", "teacher", "admin")
def page(lesson_id, page_index):
    lesson = Lesson.query.get_or_404(lesson_id)
    pages = flatten_pages(load_toc())
    if page_index < 0 or page_index >= len(pages):
        abort(404)

    item = pages[page_index]
    state = LessonTextbookState.query.filter_by(lesson_id=lesson.id).first()
    study_mode = state.study_mode if state else "textbook"
    right_page_index = page_index + 1 if page_index + 1 < len(pages) else None
    right_page = pages[right_page_index] if right_page_index is not None else None

    return render_template(
        "textbook/book.html",
        lesson=lesson,
        student_name=current_user.name,
        page=item,
        page_index=page_index,
        right_page=right_page,
        right_page_index=right_page_index,
        right_content=render_markdown(resolve_page_path(right_page_index, right_page)) if right_page else "",
        practice_tasks=build_practice_tasks(page_index, item),
        study_mode=study_mode,
        assigned_title=state.assigned_title if state else "",
        total=len(pages),
        pages=pages,
        content=render_markdown(resolve_page_path(page_index, item)),
        prev_index=page_index - 2 if page_index > 1 else (0 if page_index == 1 else None),
        next_index=page_index + 2 if page_index + 2 < len(pages) else None,
        demo_mode=False,
        activity_url=url_for("events.textbook_activity", lesson_id=lesson.id),
        status_url=url_for("lessons.status", lesson_id=lesson.id),
        homework_url=url_for("textbook.homework_upload", lesson_id=lesson.id),
        answer_url=url_for("textbook.submit_answer", lesson_id=lesson.id),
    )


@textbook_bp.post("/lesson/<int:lesson_id>/homework")
@roles_required("student")
def homework_upload(lesson_id):
    Lesson.query.get_or_404(lesson_id)
    uploaded = request.files.get("homework")
    if not uploaded or not uploaded.filename:
        return jsonify({"ok": False, "error": "file_required"}), 400

    folder = Path(current_app.instance_path) / "homework_uploads" / str(lesson_id) / str(current_user.id)
    folder.mkdir(parents=True, exist_ok=True)
    filename = secure_filename(uploaded.filename) or "homework.bin"
    target = folder / filename
    uploaded.save(target)
    return jsonify({"ok": True, "filename": uploaded.filename})


@textbook_bp.post("/lesson/<int:lesson_id>/answer")
@roles_required("student")
def submit_answer(lesson_id):
    Lesson.query.get_or_404(lesson_id)
    payload = request.get_json(silent=True) or {}
    page_index = int(payload.get("page_index", 0))
    task_key = str(payload.get("task_key", "")).strip()
    answer_text = str(payload.get("answer", "")).strip()
    expected = str(payload.get("expected", "")).strip()
    if not task_key or not answer_text:
        return jsonify({"ok": False, "error": "answer_required"}), 400

    is_correct = None
    if expected:
        is_correct = normalize_answer(answer_text) == normalize_answer(expected)

    db.session.add(
        TextbookAnswer(
            lesson_id=lesson_id,
            student_id=current_user.id,
            page_index=page_index,
            task_key=task_key,
            answer_text=answer_text,
            is_correct=is_correct,
        )
    )
    db.session.add(
        TextbookActivity(
            lesson_id=lesson_id,
            student_id=current_user.id,
            page_index=page_index,
            action="answer_submitted",
            payload_json=json.dumps({"task_key": task_key, "is_correct": is_correct}, ensure_ascii=False),
        )
    )
    db.session.commit()

    if is_correct is True:
        message = "Ответ сохранен. Верно, можно двигаться дальше."
    elif is_correct is False:
        message = "Ответ сохранен. Проверь рассуждение и попробуй исправить."
    else:
        message = "Ответ сохранен. Учитель увидит его в активности урока."
    return jsonify({"ok": True, "is_correct": is_correct, "message": message})


def load_toc():
    path = current_app.config["TEXTBOOK_DIR"] / "toc.json"
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_pages(toc):
    result = []
    for chapter in toc.get("chapters", []):
        for topic in chapter.get("topics", []):
            result.append(
                {
                    "chapter": chapter.get("title", ""),
                    "title": topic.get("title", ""),
                    "file": topic.get("file", ""),
                }
            )
    return result


def render_markdown(path):
    if not path.exists():
        return "<h1>Страница учебника не найдена</h1>"
    text = path.read_text(encoding="utf-8")
    return markdown.markdown(text, extensions=["tables", "fenced_code"])


def resolve_page_path(page_index, item):
    pages_dir = current_app.config["TEXTBOOK_DIR"] / "pages"
    toc_path = pages_dir / Path(item["file"]).name
    if toc_path.exists():
        return toc_path

    prefix = f"{page_index + 1:02d}_"
    matches = sorted(path for path in pages_dir.glob("*.md") if path.name.startswith(prefix))
    if matches:
        return matches[0]

    all_pages = sorted(pages_dir.glob("*.md"))
    if 0 <= page_index < len(all_pages):
        return all_pages[page_index]
    return toc_path


def build_practice_tasks(page_index, page):
    title = page.get("title", "тема")
    if "отриц" in title.lower():
        return [
            {
                "key": f"p{page_index}-neg-1",
                "title": "Самостоятельно 1",
                "prompt": "Запиши отрицание высказывания: «Все ученики решили задачу».",
                "expected": "Не все ученики решили задачу",
            },
            {
                "key": f"p{page_index}-neg-2",
                "title": "Самостоятельно 2",
                "prompt": "Истинно ли отрицание фразы «число 12 делится на 3», если написать «число 12 не делится на 3»?",
                "expected": "нет",
            },
            {
                "key": f"p{page_index}-neg-3",
                "title": "Развернутый ответ",
                "prompt": "Объясни своими словами, почему квантор «все» нельзя отрицать простой частицей «не» без проверки смысла.",
                "expected": "",
            },
        ]
    return [
        {
            "key": f"p{page_index}-base-1",
            "title": "Самостоятельно 1",
            "prompt": f"Сформулируй главное правило темы «{title}» одним предложением.",
            "expected": "",
        },
        {
            "key": f"p{page_index}-base-2",
            "title": "Самостоятельно 2",
            "prompt": "Придумай короткий пример к этой теме и запиши решение.",
            "expected": "",
        },
        {
            "key": f"p{page_index}-base-3",
            "title": "Проверка понимания",
            "prompt": "Что в этой теме кажется самым сложным? Напиши вопрос для учителя.",
            "expected": "",
        },
    ]


def normalize_answer(value):
    text = value.lower().replace("ё", "е")
    text = re.sub(r"[^а-яa-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()
