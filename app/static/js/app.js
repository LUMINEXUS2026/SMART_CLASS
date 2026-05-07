(() => {
  const clock = document.querySelector("[data-clock]");
  if (!clock) return;

  function tick() {
    clock.textContent = new Date().toLocaleTimeString("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    });
  }

  tick();
  setInterval(tick, 1000);
})();

(() => {
  const toggle = document.querySelector("[data-theme-toggle]");
  if (!toggle) return;

  const icon = toggle.querySelector("[data-theme-icon]");
  const label = toggle.querySelector("[data-theme-text]");

  function applyTheme(theme) {
    const isLight = theme === "light";
    document.documentElement.dataset.theme = isLight ? "light" : "dark";
    localStorage.setItem("educam-theme", isLight ? "light" : "dark");
    if (icon) icon.textContent = isLight ? "Sun" : "Night";
    if (label) label.textContent = isLight ? "Светлая" : "Темная";
    toggle.setAttribute("aria-pressed", String(isLight));
    toggle.title = isLight ? "Включить темную тему" : "Включить светлую тему";
  }

  applyTheme(localStorage.getItem("educam-theme") || "dark");

  toggle.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
    applyTheme(next);
  });
})();
