'use strict';

// Recorded source-frame values, not interpolated distance or model predictions.
// Native WebVTT is retained for fullscreen and for a no-enhancement fallback.
(() => {
  const root = document.getElementById('demo');
  if (!root) return;
  const data = window.SPACE_VIDEO_CONTEXT;
  const button = root.querySelector('[data-distance-captions]');
  const cards = Array.from(root.querySelectorAll('[data-video-card]'));
  if (!data || !button || !Array.isArray(data.clips)) return;
  const zh = document.documentElement.lang === 'zh-CN';
  const entries = cards.map(card => ({
    card, video: card.querySelector('video'), track: card.querySelector('track'),
    hud: card.querySelector('[data-video-context]'),
    value: card.querySelector('[data-context-distance]'),
    state: card.querySelector('[data-context-state]'),
    clip: data.clips.find(clip => clip.world === card.dataset.videoCard),
    frameCallback: null, lastFrame: -1, nativeFullscreen: false,
  }));
  if (entries.some(e => !e.video || !e.track?.track || !e.hud || !e.value || !e.state ||
      !e.clip?.frames?.length || !e.clip.frames.every(f => Number.isFinite(f.distance_m) && f.end_ms > f.start_ms))) return;
  let enabled = true;
  const expectedModes = new WeakMap();
  const active = e => e.card.classList.contains('is-active');
  const nativeScreen = e => e.nativeFullscreen || e.video.webkitDisplayingFullscreen ||
    document.fullscreenElement === e.video || document.webkitFullscreenElement === e.video;

  function stateText(frame, radius) {
    if (zh) return frame.inside_R ? `已进入 ${radius} m 范围` : frame.state === 'after' ? `已离开 ${radius} m 范围` : `${radius} m 范围之外`;
    return frame.inside_R ? `Within ${radius} m range` : frame.state === 'after' ? `Beyond ${radius} m again` : `Outside ${radius} m range`;
  }

  function frameAt(clip, seconds) {
    const ms = Math.max(0, (Number.isFinite(seconds) ? seconds : 0) * 1000 + 1e-7);
    // Select an actual recorded frame, including while seeking backwards.
    let low = 0, high = clip.frames.length;
    while (low + 1 < high) {
      const mid = Math.floor((low + high) / 2);
      if (clip.frames[mid].start_ms <= ms) low = mid; else high = mid;
    }
    return clip.frames[low];
  }

  function sync(e, seconds = e.video.currentTime) {
    const frame = frameAt(e.clip, seconds);
    if (frame.frame_idx !== e.lastFrame) {
      e.value.textContent = frame.distance_m.toFixed(2);
      e.state.textContent = stateText(frame, e.clip.success_radius_m);
      e.hud.dataset.range = frame.state;
      e.hud.dataset.frame = String(frame.frame_idx);
      e.lastFrame = frame.frame_idx;
    }
    e.hud.hidden = !enabled || !active(e) || !!nativeScreen(e);
  }

  function cancelFrame(e) {
    if (e.frameCallback !== null && e.video.cancelVideoFrameCallback) e.video.cancelVideoFrameCallback(e.frameCallback);
    e.frameCallback = null;
  }

  function followFrames(e) {
    if (e.frameCallback !== null || !e.video.requestVideoFrameCallback || e.video.paused || !active(e) || document.hidden || !enabled) return;
    e.frameCallback = e.video.requestVideoFrameCallback((_, metadata) => {
      e.frameCallback = null;
      sync(e, metadata.mediaTime);
      followFrames(e);
    });
  }

  function apply() {
    entries.forEach(e => {
      const mode = enabled && active(e) ? (nativeScreen(e) ? 'showing' : 'hidden') : 'disabled';
      // TextTrackList change is asynchronous; remember intended modes to avoid
      // mistaking our hidden native track for a user turning captions off.
      expectedModes.set(e.track.track, mode);
      if (e.track.track.mode !== mode) e.track.track.mode = mode;
      sync(e);
      if (!enabled || !active(e)) cancelFrame(e); else followFrames(e);
    });
    button.setAttribute('aria-pressed', String(enabled));
    button.textContent = zh ? `距离信息：${enabled ? '开' : '关'}` : `Distance overlay: ${enabled ? 'on' : 'off'}`;
  }

  button.addEventListener('click', () => { enabled = !enabled; apply(); });
  root.addEventListener('video-scene-change', apply);
  document.addEventListener('fullscreenchange', apply);
  document.addEventListener('webkitfullscreenchange', apply);
  document.addEventListener('visibilitychange', () => {
    entries.forEach(e => document.hidden ? cancelFrame(e) : followFrames(e));
  });

  entries.forEach(e => {
    for (const event of ['loadedmetadata', 'loadeddata', 'timeupdate', 'seeking', 'seeked', 'ended', 'emptied']) {
      e.video.addEventListener(event, () => sync(e));
    }
    e.video.addEventListener('play', () => followFrames(e));
    e.video.addEventListener('pause', () => { cancelFrame(e); sync(e); });
    e.video.addEventListener('webkitbeginfullscreen', () => { e.nativeFullscreen = true; apply(); });
    e.video.addEventListener('webkitendfullscreen', () => { e.nativeFullscreen = false; apply(); });
    e.video.textTracks.addEventListener('change', () => {
      if (!active(e) || e.track.track.mode === expectedModes.get(e.track.track)) return;
      if (e.track.track.mode === 'showing') enabled = true;
      else if (e.track.track.mode === 'disabled') enabled = false;
      apply();
    });
    e.track.addEventListener('load', apply);
    e.track.addEventListener('error', () => {
      if (active(e) && nativeScreen(e)) root.querySelector('[data-video-status]').textContent = zh
        ? '全屏字幕暂时无法加载，可退出全屏查看距离信息。'
        : 'Fullscreen captions could not load. Exit fullscreen to view the distance overlay.';
    });
  });
  button.hidden = false;
  apply();
})();
