(function () {
  const stage = document.querySelector("[data-state-url]");
  if (!stage) return;

  const stateUrl = stage.dataset.stateUrl;
  const video = stage.querySelector(".lesson-video");
  const liveSnapshot = video.hasAttribute("data-live-snapshot");
  const freePlayVideo = video.hasAttribute("data-free-play-video");
  const aiPaced = video.hasAttribute("data-ai-paced-video");
  const smoothVideo = video.hasAttribute("data-smooth-video");
  const smoothSyncVideo = video.hasAttribute("data-smooth-sync-video");
  const steppedAiVideo = video.hasAttribute("data-stepped-ai-video");
  const syncLag = Number(video.dataset.syncLag || 0.75);
  const stepFrames = Math.max(1, Number(video.dataset.stepFrames || 4));
  let steppedTarget = 0;
  let lastStepAt = 0;
  let lastSnapshotVersion = "";
  let latestState = null;
  const canvas = stage.querySelector("[data-camera-canvas]");
  const context = canvas ? canvas.getContext("2d") : null;
  const overlay = stage.querySelector("[data-camera-overlay]");
  const attentionChip = stage.querySelector("[data-attention-chip]");
  const detectionChip = stage.querySelector("[data-detection-chip]");
  const recognitionList = document.querySelector("[data-recognition-list]");
  const demoTeacherKeyframes = [
    [0, [1185, 365, 235, 430]],
    [45, [1235, 385, 230, 425]],
    [95, [1265, 382, 225, 430]],
    [150, [1295, 388, 220, 430]],
    [210, [1320, 384, 215, 435]],
    [248, [1310, 386, 215, 435]],
    [285, [1275, 390, 220, 428]],
    [316, [1185, 365, 235, 430]],
  ];
  if (liveSnapshot) {
    video.addEventListener("load", () => {
      video.style.opacity = "1";
    });
  }
  if (freePlayVideo) {
    const startVideo = () => {
      video.play().catch(() => {});
    };
    video.addEventListener("loadeddata", startVideo);
    video.addEventListener("canplay", startVideo);
    startVideo();
  }

  function formatPercent(value) {
    if (value === null || value === undefined || Number.isNaN(Number(value))) {
      return "AI waiting";
    }
    return `${Math.round(Number(value))}% ATTENTION`;
  }

  function severityFor(item) {
    if (item.label === "cell phone" || item.role === "phone") return "warning";
    if (item.role === "teacher") return "success";
    return "info";
  }

  function classNameFor(item) {
    return `ai-live-box ai-live-box-${item.role || item.label || "object"}`.replace(/\s+/g, "-");
  }

  function colorFor(item) {
    if (item.label === "cell phone" || item.role === "phone") return "rgba(245, 158, 11, 0.72)";
    if (item.role === "teacher") return "rgba(14, 165, 233, 0.74)";
    if (item.role === "student") return "rgba(34, 197, 94, 0.58)";
    return "rgba(52, 211, 153, 0.52)";
  }

  function labelFor(item) {
    const confidence = Math.round((item.confidence || 0) * 100);
    const name = item.name || item.display_name;
    if (item.role === "teacher") return `${name || "Учитель"} ${confidence}%`;
    if (item.role === "student") {
      const attention = item.attention ? ` · ${Math.round(item.attention)}% вним.` : "";
      return `${name || "Не распознанный человек"} ${confidence}%${attention}`;
    }
    if (item.label === "cell phone") return `Телефон ${confidence}%`;
    if (name) return `${name} ${confidence}%`;
    return `${item.label || "Объект"} ${confidence}%`;
  }

  function videoRect(frameWidth, frameHeight) {
    const stageRect = stage.getBoundingClientRect();
    const videoRect = video.getBoundingClientRect();
    const width = frameWidth || video.videoWidth || videoRect.width;
    const height = frameHeight || video.videoHeight || videoRect.height;
    const videoRatio = width / height;
    const elementRatio = videoRect.width / videoRect.height;
    let renderWidth = videoRect.width;
    let renderHeight = videoRect.height;
    let offsetX = videoRect.left - stageRect.left;
    let offsetY = videoRect.top - stageRect.top;

    if (elementRatio > videoRatio) {
      renderWidth = videoRect.height * videoRatio;
      offsetX += (videoRect.width - renderWidth) / 2;
    } else {
      renderHeight = videoRect.width / videoRatio;
      offsetY += (videoRect.height - renderHeight) / 2;
    }

    return { offsetX, offsetY, renderWidth, renderHeight, width, height };
  }

  function interpolateBox(time, keyframes) {
    for (let index = 0; index < keyframes.length - 1; index += 1) {
      const [timeA, boxA] = keyframes[index];
      const [timeB, boxB] = keyframes[index + 1];
      if (time >= timeA && time <= timeB) {
        const progress = (time - timeA) / Math.max(timeB - timeA, 1);
        const eased = progress * progress * (3 - 2 * progress);
        return boxA.map((value, item) => Math.round(value + (boxB[item] - value) * eased));
      }
    }
    return keyframes[keyframes.length - 1][1].slice();
  }

  function demoTeacherBox() {
    const videoTime = Number.isFinite(video.currentTime) ? video.currentTime : 0;
    const box = interpolateBox(videoTime, demoTeacherKeyframes);
    box[0] += Math.round(Math.sin(videoTime * 2.1) * 3);
    box[1] += Math.round(Math.cos(videoTime * 1.7) * 2);
    return box;
  }

  function stateWithDemoTeacherPath(state) {
    if (liveSnapshot || !Number.isFinite(video.currentTime)) return state;
    const nextState = { ...state };
    nextState.detections = (state.detections || []).map((item) => (
      item.role === "teacher" ? { ...item, box: demoTeacherBox() } : item
    ));
    nextState.recognitions = (state.recognitions || []).map((item) => (
      item.role === "teacher" ? { ...item, box: demoTeacherBox() } : item
    ));
    return nextState;
  }

  function renderBoxes(state) {
    overlay.replaceChildren();
    const frame = videoRect(state.frame_width, state.frame_height);
    drawCanvasBoxes(state, frame);
  }

  function drawCanvasBoxes(state, frame) {
    if (!canvas || !context) return;

    const stageRect = stage.getBoundingClientRect();
    const scale = window.devicePixelRatio || 1;
    canvas.width = Math.max(1, Math.round(stageRect.width * scale));
    canvas.height = Math.max(1, Math.round(stageRect.height * scale));
    context.setTransform(scale, 0, 0, scale, 0, 0);
    context.clearRect(0, 0, stageRect.width, stageRect.height);

    (state.detections || []).forEach((item) => {
      if (!Array.isArray(item.box) || item.box.length !== 4) return;
      const [x, y, w, h] = item.box;
      const left = frame.offsetX + (x / frame.width) * frame.renderWidth;
      const top = frame.offsetY + (y / frame.height) * frame.renderHeight;
      const width = (w / frame.width) * frame.renderWidth;
      const height = (h / frame.height) * frame.renderHeight;
      const color = colorFor(item);
      const label = labelFor(item);

      context.lineWidth = item.role === "teacher" ? 2 : 1.5;
      context.strokeStyle = color;
      context.fillStyle = "rgba(5, 8, 22, 0.58)";
      context.strokeRect(left, top, width, height);

      context.font = "650 11px system-ui, -apple-system, Segoe UI, sans-serif";
      const labelWidth = Math.min(context.measureText(label).width + 14, Math.max(width, 90));
      context.fillStyle = color;
      context.fillRect(left, Math.max(0, top - 20), labelWidth, 20);
      context.fillStyle = "#ffffff";
      context.fillText(label, left + 7, Math.max(14, top - 6));
    });
  }

  function renderRecognitionList(state) {
    const behaviorEvents = state.events || [];
    const attentionRows = state.student_attention || [];
    const items = state.recognitions && state.recognitions.length ? state.recognitions : state.detections || [];
    recognitionList.replaceChildren();

    behaviorEvents.slice(0, 3).forEach((event) => {
      const card = document.createElement("div");
      card.className = "event-card compact";
      card.innerHTML = `<span class="severity ${event.level || "info"}">${event.type || "event"}</span><strong>${event.title}</strong><span>${event.text || ""}</span>`;
      recognitionList.appendChild(card);
    });

    attentionRows.slice(0, 4).forEach((row) => {
      const card = document.createElement("div");
      card.className = "event-card compact";
      const status = row.status === "occluded_by_teacher" ? "закрыт учителем" : row.status === "visible" ? "в кадре" : "не виден";
      const attention = row.attention === null || row.attention === undefined ? "—" : `${Math.round(row.attention)}%`;
      card.innerHTML = `<span class="severity info">attention</span><strong>${row.student}: ${attention}</strong><span>${status}</span>`;
      recognitionList.appendChild(card);
    });

    if (!items.length) {
      const card = document.createElement("div");
      card.className = "event-card compact";
      card.innerHTML = `<span class="severity info">status</span><strong>${state.message || "AI-воркер не прислал detections"}</strong><span>Страница подключена к реальному состоянию камеры.</span>`;
      recognitionList.appendChild(card);
      return;
    }

    items.slice(0, 8).forEach((item) => {
      const card = document.createElement("div");
      card.className = "event-card compact";
      card.innerHTML = `<span class="severity ${severityFor(item)}">${item.role || item.label || "AI"}</span><strong>${labelFor(item)}</strong><span>${item.detail || item.label || "Распознано моделью"}</span>`;
      recognitionList.appendChild(card);
    });
  }

  async function refreshState() {
    try {
      const response = await fetch(stateUrl, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const state = await response.json();
      if (liveSnapshot) {
        const snapshotVersion = String(state.updated_at || "");
        if (snapshotVersion && snapshotVersion !== lastSnapshotVersion) {
          lastSnapshotVersion = snapshotVersion;
          const cleanSrc = video.getAttribute("src").split("?")[0];
          video.setAttribute("src", `${cleanSrc}?t=${encodeURIComponent(snapshotVersion)}`);
        }
      }
      if (aiPaced && !video.paused) {
        video.pause();
      }
      if (smoothSyncVideo && Number.isFinite(Number(state.video_time_sec)) && Number.isFinite(video.duration)) {
        const targetTime = Math.min(Math.max(0, Number(state.video_time_sec) - syncLag), Math.max(0, video.duration - 0.2));
        const drift = video.currentTime - targetTime;
        if (Math.abs(drift) > 1.6) {
          video.currentTime = targetTime;
          video.playbackRate = 1;
        } else if (drift > 0.55) {
          video.playbackRate = 0.82;
        } else if (drift < -0.55) {
          video.playbackRate = 1.16;
        } else {
          video.playbackRate = 1;
        }
        if (video.paused) {
          video.play().catch(() => {});
        }
      }

      if (steppedAiVideo && Number.isFinite(Number(state.video_time_sec)) && Number.isFinite(video.duration)) {
        steppedTarget = Math.min(Number(state.video_time_sec), Math.max(0, video.duration - 0.2));
        if (!video.paused) {
          video.pause();
        }
        if (Math.abs(video.currentTime - steppedTarget) > 2) {
          video.currentTime = steppedTarget;
        }
      }

      if (!freePlayVideo && !smoothVideo && !smoothSyncVideo && !steppedAiVideo && (
        Number.isFinite(Number(state.video_time_sec)) &&
        Number.isFinite(video.duration)
      )) {
        const targetTime = Math.min(Number(state.video_time_sec), Math.max(0, video.duration - 0.2));
        if (aiPaced || Math.abs(video.currentTime - targetTime) > 1.4) {
          video.currentTime = targetTime;
        }
      }
      const renderState = stateWithDemoTeacherPath(state);
      latestState = state;
      attentionChip.textContent = formatPercent(renderState.attention);
      detectionChip.textContent = `${renderState.people_count || 0} persons · ${renderState.phones_count || 0} phones`;
      renderBoxes(renderState);
      renderRecognitionList(renderState);
    } catch (error) {
      overlay.replaceChildren();
      if (context) context.clearRect(0, 0, canvas.width, canvas.height);
      attentionChip.textContent = "AI offline";
      detectionChip.textContent = "state unavailable";
      recognitionList.innerHTML = `<div class="event-card compact"><span class="severity critical">error</span><strong>Нет связи с AI-состоянием</strong><span>${error.message}</span></div>`;
    }
  }

  video.addEventListener(liveSnapshot ? "load" : "loadedmetadata", refreshState);
  window.addEventListener("resize", refreshState);

  function animateSteppedVideo(now) {
    if (steppedAiVideo && Number.isFinite(video.duration)) {
      const minInterval = 1000 / Math.max(6, Math.min(18, stepFrames * 3));
      if (now - lastStepAt >= minInterval) {
        const delta = steppedTarget - video.currentTime;
        if (Math.abs(delta) > 0.025) {
          video.currentTime += delta / stepFrames;
        }
        lastStepAt = now;
      }
    }
    if (!liveSnapshot && !steppedAiVideo && latestState) {
      renderBoxes(stateWithDemoTeacherPath(latestState));
    }
    window.requestAnimationFrame(animateSteppedVideo);
  }

  refreshState();
  window.requestAnimationFrame(animateSteppedVideo);
  window.setInterval(refreshState, smoothVideo || smoothSyncVideo ? 700 : 450);
})();
