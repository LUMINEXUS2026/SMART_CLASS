(() => {
  // =========================
  // 1) АНИМАЦИЯ ПЕРЕЛИСТЫВАНИЯ
  // =========================
  const spread = document.getElementById("spread");
  let currentController = null;

  function runPageCurlThenGo(href) {
    if (!spread) {
      window.location.href = href;
      return;
    }
    spread.classList.remove("is-page-curl");
    void spread.offsetWidth;
    spread.classList.add("is-page-curl");
    setTimeout(() => {
      window.location.href = href;
    }, 420);
  }

  // =========================
  // 2) МОДАЛКА ИИ (ЧАТ)
  // =========================
  const AI = {
    topic: "",
    taskNum: "",
    taskText: "",
    imageDataUrl: ""
  };

  function openAiModal() {
    const m = document.getElementById("aiModal");
    if (!m) return;
    m.style.display = "block";

    const meta = document.getElementById("aiMeta");
    const task = document.getElementById("aiTaskText");
    const chat = document.getElementById("aiChat");
    const inp = document.getElementById("aiUserInput");
    const hint = document.getElementById("aiFileHint");
    const file = document.getElementById("aiFile");

    if (meta) meta.textContent = `${AI.topic} • Задание №${AI.taskNum}`;
    if (task) task.textContent = AI.taskText || "(текст задания не передан)";
    if (chat) chat.innerHTML = "";
    if (inp) inp.value = "";
    if (hint) {
      hint.style.display = "none";
      hint.textContent = "";
    }
    if (file) file.value = "";
    AI.imageDataUrl = "";
  }

  function closeAiModal() {
    const m = document.getElementById("aiModal");
    if (!m) return;
    m.style.display = "none";
  }

  function addMsg(role, text, isHtml = false) {
    const chat = document.getElementById("aiChat");
    if (!chat) return;

    const div = document.createElement("div");
    div.className = "msg " + (role === "user" ? "user" : "ai");

    if (isHtml) {
      div.innerHTML = text;
    } else {
      div.textContent = text;
    }

    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
  }

  async function askAI(level, extraText = "") {
    const promptText = extraText
      ? extraText
      : level === 1
        ? "Объясни на аналогичном примере."
        : level === 2
          ? "Объясни попроще."
          : "Объясни ещё проще.";

    addMsg("user", promptText);
    addMsg("ai", "Думаю…");

    const payload = {
      topic_title: AI.topic,
      task_number: AI.taskNum,
      task_text: AI.taskText,
      level: level,
      extra: extraText,
      image: AI.imageDataUrl || ""
    };

    if (currentController) {
      currentController.abort();
    }
    currentController = new AbortController();

    try {
      const res = await fetch("/ai/explain", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: currentController.signal
      });

      const data = await res.json();

      const chat = document.getElementById("aiChat");
      if (chat && chat.lastChild) {
        chat.removeChild(chat.lastChild);
      }

      if (!data.ok) {
        addMsg("ai", data.error || "Ошибка.");
        currentController = null;
        return;
      }

      addMsg("ai", data.html || data.text, true);

      if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise();
      }

      currentController = null;
    } catch (e) {
      const chat = document.getElementById("aiChat");
      if (chat && chat.lastChild) {
        chat.removeChild(chat.lastChild);
      }

      if (e.name === "AbortError") {
        addMsg("ai", "Генерация остановлена.");
      } else {
        addMsg("ai", "Ошибка соединения с сервером.");
      }

      currentController = null;
    }
  }

  async function checkAnswer(studentText) {
    addMsg("user", "Проверь моё решение.");
    addMsg("ai", "Проверяю…");

    const payload = {
      topic_title: AI.topic,
      task_number: AI.taskNum,
      task_text: AI.taskText,
      student_answer: studentText,
      image: AI.imageDataUrl || ""
    };

    if (currentController) {
      currentController.abort();
    }
    currentController = new AbortController();

    try {
      const res = await fetch("/ai/check", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
        signal: currentController.signal
      });

      const data = await res.json();

      const chat = document.getElementById("aiChat");
      if (chat && chat.lastChild) {
        chat.removeChild(chat.lastChild);
      }

      if (!data.ok) {
        addMsg("ai", data.error || "Ошибка проверки.");
        currentController = null;
        return;
      }

      addMsg("ai", data.html || data.text, true);

      if (window.MathJax && window.MathJax.typesetPromise) {
        window.MathJax.typesetPromise();
      }

      currentController = null;
    } catch (e) {
      const chat = document.getElementById("aiChat");
      if (chat && chat.lastChild) {
        chat.removeChild(chat.lastChild);
      }

      if (e.name === "AbortError") {
        addMsg("ai", "Проверка остановлена.");
      } else {
        addMsg("ai", "Ошибка соединения с сервером.");
      }

      currentController = null;
    }
  }

  // =========================
  // 3) ОБРАБОТЧИКИ СОБЫТИЙ
  // =========================

  // Навигация
  document.addEventListener("click", (e) => {
    const nav = e.target.closest("a[data-nav]");
    if (!nav) return;

    if (nav.classList.contains("is-disabled")) {
      e.preventDefault();
      return;
    }

    const href = nav.getAttribute("href");
    if (!href || href === "#") return;

    e.preventDefault();
    runPageCurlThenGo(href);
  });

  // Кнопка рядом с заданием
  document.addEventListener("click", (e) => {
    const ask = e.target.closest(".askAI");
    if (!ask) return;

    AI.topic = ask.getAttribute("data-topic") || "Тема";
    AI.taskNum = ask.getAttribute("data-task") || "?";
    AI.taskText = ask.getAttribute("data-text") || "";

    openAiModal();
    askAI(1);
  });

  // Управление модалкой
  document.addEventListener("click", (e) => {
    if (e.target.id === "aiClose" || e.target.classList.contains("aiModal__backdrop")) {
      closeAiModal();
      return;
    }

    if (e.target.id === "aiBtnExplain") {
      askAI(1);
      return;
    }

    if (e.target.id === "aiBtnSimpler") {
      askAI(2);
      return;
    }

    if (e.target.id === "aiBtnSimplest") {
      askAI(3);
      return;
    }

    if (e.target.id === "aiBtnCheck") {
      const inp = document.getElementById("aiUserInput");
      const txt = (inp?.value || "").trim();

      if (!txt && !AI.imageDataUrl) {
        addMsg("ai", "Пришли текст решения или прикрепи фото.");
        return;
      }

      checkAnswer(txt);
      return;
    }

    if (e.target.id === "aiBtnStop") {
      if (currentController) {
        currentController.abort();
      }
      return;
    }

    if (e.target.id === "aiSend") {
      const inp = document.getElementById("aiUserInput");
      const txt = (inp?.value || "").trim();

      if (!txt) return;

      inp.value = "";
      askAI(2, txt);
    }
  });

  // Прикрепление картинки
  document.addEventListener("change", (e) => {
    if (!e.target || e.target.id !== "aiFile") return;

    const file = e.target.files && e.target.files[0];
    if (!file) return;

    const hint = document.getElementById("aiFileHint");
    const reader = new FileReader();

    reader.onload = () => {
      AI.imageDataUrl = reader.result;
      if (hint) {
        hint.style.display = "block";
        hint.textContent = `Прикреплено изображение: ${file.name}`;
      }
    };

    reader.readAsDataURL(file);
  });
})();

// =========================
// 4) DRAG & DROP МОДАЛКИ
// =========================
(() => {
  const panel = document.getElementById("aiPanel");
  const handle = document.getElementById("aiDragHandle");
  if (!panel || !handle) return;

  let dragging = false;
  let startX = 0;
  let startY = 0;
  let startLeft = 0;
  let startTop = 0;

  handle.addEventListener("mousedown", (e) => {
    if (e.target && e.target.closest("#aiClose")) return;

    dragging = true;
    startX = e.clientX;
    startY = e.clientY;

    const rect = panel.getBoundingClientRect();
    startLeft = rect.left;
    startTop = rect.top;

    panel.style.position = "fixed";
    panel.style.left = startLeft + "px";
    panel.style.top = startTop + "px";
    panel.style.right = "auto";
    panel.style.bottom = "auto";

    e.preventDefault();
  });

  window.addEventListener("mousemove", (e) => {
    if (!dragging) return;

    const dx = e.clientX - startX;
    const dy = e.clientY - startY;

    let newLeft = startLeft + dx;
    let newTop = startTop + dy;

    const margin = 10;
    const rect = panel.getBoundingClientRect();
    const maxLeft = window.innerWidth - rect.width - margin;
    const maxTop = window.innerHeight - rect.height - margin;

    newLeft = Math.max(margin, Math.min(maxLeft, newLeft));
    newTop = Math.max(margin, Math.min(maxTop, newTop));

    panel.style.left = newLeft + "px";
    panel.style.top = newTop + "px";
  });

  window.addEventListener("mouseup", () => {
    dragging = false;
  });
})();