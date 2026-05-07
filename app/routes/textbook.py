import json
from pathlib import Path

import markdown
from flask import Blueprint, abort, current_app, render_template, url_for
from flask_login import current_user

from app.models import Lesson
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
    html = render_markdown(resolve_page_path(page_index, item))
    return render_template(
        "textbook/book.html",
        lesson=lesson,
        student_name=current_user.name,
        page=item,
        page_index=page_index,
        total=len(pages),
        pages=pages,
        content=html,
        prev_index=page_index - 1 if page_index > 0 else None,
        next_index=page_index + 1 if page_index < len(pages) - 1 else None,
        demo_mode=False,
        activity_url=url_for("events.textbook_activity", lesson_id=lesson.id),
        status_url=url_for("lessons.status", lesson_id=lesson.id),
    )


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
