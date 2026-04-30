(() => {
  const shell = document.querySelector(".lesson-shell[data-lesson-id]");
  const list = document.getElementById("eventList");
  if (!shell || !list) return;

  async function refreshEvents() {
    const response = await fetch(shell.dataset.eventsUrl);
    const events = await response.json();
    list.innerHTML = events.map((event) => {
      const time = new Date(event.created_at).toLocaleTimeString();
      const student = event.student ? ` · ${event.student}` : "";
      const tone = event.event_type.includes("left") ? " warning" : "";
      return `<div class="event-card">
        <span class="severity${tone}">${event.event_type}</span>
        <strong>${event.student || "Система"}</strong>
        <span>${time}${student} · ${event.source}</span>
      </div>`;
    }).join("");
  }

  setInterval(refreshEvents, 3000);
})();
