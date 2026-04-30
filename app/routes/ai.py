from flask import Blueprint, jsonify, request

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


@ai_bp.post("/explain")
def explain():
    data = request.get_json(force=True)
    topic = (data.get("topic_title") or "Математика 6 класс").strip()
    task = (data.get("task_text") or "текущее задание").strip()
    question = (data.get("question") or "").strip()

    answer = (
        f"**Тема:** {topic}\n\n"
        "1. Сначала найди, что известно в условии.\n"
        "2. Потом запиши, что нужно доказать или посчитать.\n"
        "3. Решай маленькими шагами и проверяй каждый шаг.\n\n"
        f"**Похожая ситуация:** возьми такое же задание, но с другими числами или словами. "
        "Разбери его по шагам, а своё задание реши самостоятельно.\n\n"
        f"**Твой вопрос:** {question or 'пока не указан'}\n\n"
        "Я не пишу готовый ответ, а помогаю понять способ решения."
    )
    return jsonify({"ok": True, "text": answer, "task": task[:800]})

