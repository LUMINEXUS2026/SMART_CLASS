(() => {
  const root = document.querySelector(".book-layout[data-lesson-id]");
  if (!root) return;

  const dialog = document.getElementById("aiDialog");
  const aiTask = document.getElementById("aiTask");
  const aiAnswer = document.getElementById("aiAnswer");
  const aiQuestion = document.getElementById("aiQuestion");
  const title = document.querySelector(".book-page h1")?.textContent?.trim() || "Математика";

  let taskText = "";

  function openHelper(text = "") {
    taskText = text || title;
    aiTask.textContent = taskText;
    aiAnswer.textContent = "Напиши вопрос или нажми кнопку ниже. Помощник даст подсказку без готового ответа.";
    if (dialog?.showModal) {
      dialog.showModal();
    } else if (dialog) {
      dialog.setAttribute("open", "open");
    }
  }

  async function askHelper(action) {
    aiAnswer.textContent = "Готовлю подсказку...";
    const response = await fetch("/api/ai/explain", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        topic_title: title,
        task_text: taskText,
        question: aiQuestion?.value || "",
        action
      })
    });
    const data = await response.json();
    aiAnswer.textContent = data.ok ? data.text.replaceAll("**", "") : "Не удалось получить подсказку.";
  }

  document.addEventListener("click", (event) => {
    const pageHelp = event.target.closest("[data-help-page]");
    if (pageHelp) {
      openHelper();
      return;
    }

    const askButton = event.target.closest(".askAI");
    if (askButton) {
      event.preventDefault();
      const text = askButton.getAttribute("data-text") || askButton.closest("p, li, section")?.textContent || title;
      openHelper(text.trim());
    }

    const aiAction = event.target.closest("[data-ai-action]");
    if (aiAction) {
      askHelper(aiAction.dataset.aiAction);
    }
  });
})();
