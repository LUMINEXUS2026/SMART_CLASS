(() => {
  const root = document.querySelector(".book-layout[data-lesson-id]");
  if (!root) return;

  const dialog = document.getElementById("aiDialog");
  const aiTask = document.getElementById("aiTask");
  const aiAnswer = document.getElementById("aiAnswer");
  const aiQuestion = document.getElementById("aiQuestion");
  const homeworkFile = document.getElementById("homeworkFile");
  const spread = document.querySelector("[data-book-spread]");
  const title = document.querySelector(".book-paper h2")?.textContent?.trim() || "Математика 6 класс";
  const homeworkUrl = root.dataset.homeworkUrl;
  const answerUrl = root.dataset.answerUrl;
  const statusUrl = root.dataset.statusUrl;
  const pageIndex = Number(root.dataset.pageIndex || 0);

  let taskText = "";
  let activeRequest = null;
  let isTurning = false;

  function openHelper(text = "") {
    taskText = text || title;
    aiTask.textContent = taskText;
    aiAnswer.textContent = "Выберите действие ниже. Я помогу понять ход решения, но не подменю вашу работу.";
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
      check: "Проверяю вашу мысль..."
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

  function cloneTurningPage(direction) {
    if (!spread) return null;
    const source = direction === "prev"
      ? spread.querySelector(".book-paper-left")
      : spread.querySelector(".book-paper-right");
    if (!source) return null;
    const clone = source.cloneNode(true);
    clone.classList.add("turning-page", direction === "prev" ? "turning-prev" : "turning-next");
    clone.style.width = `${source.offsetWidth}px`;
    clone.style.height = `${source.offsetHeight}px`;
    clone.style.top = `${source.offsetTop}px`;
    clone.style.left = `${source.offsetLeft}px`;
    spread.appendChild(clone);
    return clone;
  }

  function turnTo(href, direction = "next") {
    if (!href || !spread || isTurning) return;
    isTurning = true;
    spread.classList.add("is-turning");
    const page = cloneTurningPage(direction);
    page?.classList.add("animate");
    setTimeout(() => {
      window.location.href = href;
    }, 920);
  }

  function pageHref(page) {
    const current = new URL(window.location.href);
    current.pathname = current.pathname.replace(/\/page\/\d+$/, `/page/${page}`);
    return current.toString();
  }

  async function syncAssignedPage() {
    if (!statusUrl) return;
    try {
      const response = await fetch(statusUrl, { cache: "no-store" });
      const data = await response.json();
      const mode = data?.textbook?.study_mode || "textbook";
      if (mode !== root.dataset.studyMode) {
        window.location.reload();
        return;
      }
      const assigned = data?.textbook?.assigned_page_index;
      if (mode === "textbook" && Number.isInteger(assigned) && assigned !== pageIndex) {
        turnTo(pageHref(assigned), assigned < pageIndex ? "prev" : "next");
      }
    } catch {
      // Manual page turning should keep working if live sync is unavailable.
    }
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

  async function submitPractice(form) {
    if (!answerUrl) return;
    const textarea = form.querySelector("textarea[name='answer']");
    const result = form.querySelector(".practice-result");
    const answer = textarea?.value?.trim() || "";
    if (!answer) {
      if (result) result.textContent = "Сначала введи ответ.";
      return;
    }
    if (result) result.textContent = "Сохраняю...";
    try {
      const response = await fetch(answerUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          page_index: pageIndex,
          task_key: form.dataset.taskKey,
          expected: form.dataset.expected || "",
          answer
        })
      });
      const data = await response.json();
      if (result) result.textContent = data.message || "Ответ сохранен.";
    } catch {
      if (result) result.textContent = "Не удалось сохранить ответ.";
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

  document.addEventListener("submit", (event) => {
    const form = event.target.closest(".practice-task");
    if (!form) return;
    event.preventDefault();
    submitPractice(form);
  });

  homeworkFile?.addEventListener("change", () => {
    uploadHomework(homeworkFile.files?.[0]);
  });

  if (root.dataset.userRole === "student") {
    setInterval(syncAssignedPage, 2500);
  }
})();
