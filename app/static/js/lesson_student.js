(() => {
  const shell = document.querySelector(".lesson-shell[data-lesson-id]");
  if (!shell) return;

  const statusUrl = shell.dataset.statusUrl;

  async function checkStatus() {
    const response = await fetch(statusUrl);
    const data = await response.json();
    if (data.status !== "active") {
      window.location.href = "/student/dashboard";
    }
  }

  setInterval(checkStatus, 4000);
})();

