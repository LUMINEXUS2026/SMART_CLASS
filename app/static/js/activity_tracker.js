(() => {
  const root = document.querySelector(".book-layout[data-lesson-id]");
  if (!root) return;

  const lessonId = root.dataset.lessonId;
  const pageIndex = Number(root.dataset.pageIndex || 0);
  const activityUrl = root.dataset.activityUrl || `/api/lessons/${lessonId}/textbook-activity`;
  const statusUrl = root.dataset.statusUrl || `/lessons/${lessonId}/status`;
  let openedAt = Date.now();
  let lastInteractionAt = Date.now();
  let longIdleSent = false;

  async function sendActivity(action, payload = {}) {
    const durationSec = Math.max(0, Math.round((Date.now() - openedAt) / 1000));
    await fetch(activityUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        action,
        page_index: pageIndex,
        duration_sec: durationSec,
        payload
      })
    }).catch(() => {});
  }

  sendActivity("page_opened");

  ["click", "keydown", "scroll", "pointermove"].forEach((eventName) => {
    document.addEventListener(eventName, () => {
      lastInteractionAt = Date.now();
      longIdleSent = false;
    }, { passive: true });
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      sendActivity("tab_hidden");
    } else {
      openedAt = Date.now();
      sendActivity("tab_visible");
    }
  });

  window.addEventListener("beforeunload", () => {
    navigator.sendBeacon?.(
      activityUrl,
      new Blob([JSON.stringify({
        action: "page_closed",
        page_index: pageIndex,
        duration_sec: Math.max(0, Math.round((Date.now() - openedAt) / 1000))
      })], { type: "application/json" })
    );
  });

  document.addEventListener("click", (event) => {
    if (event.target.closest(".askAI")) {
      sendActivity("help_requested");
    }
    if (event.target.closest("[data-task-start]")) {
      sendActivity("task_started");
    }
    if (event.target.closest("[data-task-complete]")) {
      sendActivity("task_completed");
    }
  });

  async function checkLessonStatus() {
    const response = await fetch(statusUrl);
    const data = await response.json();
    if (data.status !== "active") {
      document.body.innerHTML = `
        <main class="page">
          <section class="panel">
            <h1>Урок завершён</h1>
            <p>Учитель завершил урок. Учебник закрыт для этой сессии.</p>
            <a class="button" href="/student/dashboard">Вернуться</a>
          </section>
        </main>
      `;
    }
  }

  setInterval(checkLessonStatus, 4000);

  setInterval(() => {
    const idleSec = Math.round((Date.now() - lastInteractionAt) / 1000);
    if (idleSec >= 90 && !longIdleSent) {
      longIdleSent = true;
      sendActivity("long_idle", { idle_sec: idleSec });
    }
  }, 15000);
})();
