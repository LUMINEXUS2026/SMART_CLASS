(() => {
  const root = document.querySelector(".book-layout[data-lesson-id]");
  if (!root) return;

  const lessonId = root.dataset.lessonId;
  const pageIndex = Number(root.dataset.pageIndex || 0);
  let openedAt = Date.now();

  async function sendActivity(action, payload = {}) {
    const durationSec = Math.max(0, Math.round((Date.now() - openedAt) / 1000));
    await fetch(`/api/lessons/${lessonId}/textbook-activity`, {
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
      `/api/lessons/${lessonId}/textbook-activity`,
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
  });
})();

