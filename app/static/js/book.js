(() => {
  const root = document.querySelector(".book-layout[data-lesson-id]");
  if (!root) return;

  const dialog = document.getElementById("aiDialog");
  const aiTask = document.getElementById("aiTask");
  const aiAnswer = document.getElementById("aiAnswer");
  const aiQuestion = document.getElementById("aiQuestion");
  const homeworkFile = document.getElementById("homeworkFile");
  const spread = document.querySelector("[data-book-spread]");
  const title = document.querySelector(".book-paper h2")?.textContent?.trim() || "Математика 6";
  const homeworkUrl = root.dataset.homeworkUrl;

  let taskText = "";
  let activeRequest = null;

  function openHelper(text = "") {
    taskText = text || title;
    aiTask.textContent = taskText;
    aiAnswer.textContent = "Выбери действие ниже. Я помогу понять ход решения, но не подменю твою работу.";
    if (dialog?.showModal) {
      dialog.showModal();
    } else if (dialog) {
      dialog.setAttribute("open", "open");
    }
  }

  async function askHelper(action) {
    if (activeRequest) activeRequest.abort();
    activeRequest = new AbortController();
    const labels = {
      explain: "Объясняю простыми словами...",
      simpler: "Делаю объяснение короче...",
      simplest: "Разбираю совсем по шагам...",
      check: "Проверяю твою мысль..."
    };
    aiAnswer.textContent = labels[action] || "Готовлю подсказку...";

    try {
      const response = await fetch("/api/ai/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: activeRequest.signal,
        body: JSON.stringify({
          topic_title: title,
          task_text: taskText,
          question: aiQuestion?.value || "",
          action
        })
      });
      const data = await response.json();
      aiAnswer.textContent = data.ok ? data.text.replaceAll("**", "") : "Не удалось получить подсказку.";
    } catch (error) {
      aiAnswer.textContent = error.name === "AbortError" ? "Остановлено." : "Помощник временно недоступен.";
    } finally {
      activeRequest = null;
    }
  }

  function turnTo(href, direction = "next") {
    if (!href) return;
    spread?.classList.add(direction === "prev" ? "is-flipping-prev" : "is-flipping-next");
    setTimeout(() => {
      window.location.href = href;
    }, 360);
  }

  async function uploadHomework(file) {
    if (!file || !homeworkUrl) return;
    const formData = new FormData();
    formData.append("homework", file);
    aiAnswer.textContent = `Прикрепляю файл: ${file.name}`;
    try {
      const response = await fetch(homeworkUrl, { method: "POST", body: formData });
      const data = await response.json();
      aiAnswer.textContent = data.ok
        ? `Файл с домашкой прикреплен: ${data.filename}`
        : "Не получилось прикрепить файл.";
    } catch {
      aiAnswer.textContent = "Не получилось прикрепить файл.";
    }
  }

  document.addEventListener("click", (event) => {
    const pageHelp = event.target.closest("[data-help-page]");
    if (pageHelp) {
      openHelper();
      return;
    }

    const turnButton = event.target.closest("[data-turn-href]");
    if (turnButton && !turnButton.disabled) {
      turnTo(turnButton.dataset.turnHref, turnButton.classList.contains("page-turn-prev") ? "prev" : "next");
      return;
    }

    const pageLink = event.target.closest("[data-page-link]");
    if (pageLink) {
      event.preventDefault();
      turnTo(pageLink.href, pageLink.textContent.toLowerCase().includes("назад") ? "prev" : "next");
      return;
    }

    const askButton = event.target.closest(".askAI");
    if (askButton) {
      event.preventDefault();
      const text = askButton.getAttribute("data-text") || askButton.closest("p, li, section")?.textContent || title;
      openHelper(text.trim());
      return;
    }

    const aiAction = event.target.closest("[data-ai-action]");
    if (aiAction) {
      askHelper(aiAction.dataset.aiAction);
      return;
    }

    if (event.target.closest("[data-ai-stop]")) {
      if (activeRequest) activeRequest.abort();
      aiAnswer.textContent = "Остановлено.";
    }
  });

  homeworkFile?.addEventListener("change", () => {
    uploadHomework(homeworkFile.files?.[0]);
  });
})();
