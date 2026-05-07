(function () {
  const snapshots = document.querySelectorAll("[data-camera-snapshot]");
  if (!snapshots.length) return;

  async function updateSnapshot(video) {
    const stateUrl = video.dataset.stateUrl;
    const lag = Number(video.dataset.lagSeconds || 30);
    if (!stateUrl || !Number.isFinite(video.duration)) return;

    const response = await fetch(stateUrl, { cache: "no-store" });
    if (!response.ok) return;
    const state = await response.json();
    const liveTime = Number(state.video_time_sec || 0);
    const target = Math.max(0, Math.min(video.duration - 0.2, liveTime - lag));

    if (Math.abs(video.currentTime - target) > 0.8) {
      video.currentTime = target;
    }
    video.pause();
  }

  snapshots.forEach((video) => {
    video.addEventListener("loadedmetadata", () => updateSnapshot(video));
    updateSnapshot(video);
    window.setInterval(() => updateSnapshot(video), 3000);
  });
})();
