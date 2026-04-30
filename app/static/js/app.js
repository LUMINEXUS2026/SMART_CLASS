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
