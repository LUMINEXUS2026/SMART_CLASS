(() => {
  const shell = document.querySelector(".lesson-shell[data-lesson-id]");
  const list = document.getElementById("eventList");
  if (!shell || !list) return;

  async function refreshEvents() {
    const lessonId = shell.dataset.lessonId;
    const response = await fetch(`/api/lessons/${lessonId}/events`);
    const events = await response.json();
    list.innerHTML = events.map((event) => {
      const time = new Date(event.created_at).toLocaleTimeString();
      const student = event.student ? ` · ${event.student}` : "";
      return `<li>${time} · ${event.event_type}${student}</li>`;
    }).join("");
  }

  setInterval(refreshEvents, 3000);
})();

