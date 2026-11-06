'use strict';

(() => {
  const root = document.getElementById('demo');
  if (!root) return;
  const cards = Array.from(root.querySelectorAll('[data-video-card]'));
  const selectors = Array.from(root.querySelectorAll('[data-select-video]'));
  const videos = cards.map(card => card.querySelector('video'));
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const isChinese = document.documentElement.lang === 'zh-CN';
  const status = root.querySelector('[data-video-status]');
  const advanceButton = root.querySelector('[data-video-advance]');
  let autoAdvance = !reducedMotion.matches;
  let active = 0;
  let inView = false;
  let initialAutoplayAttempted = false;
  const media = videos.map(video => ({
    candidates: [
      {url: video.dataset.webm, type: 'video/webm; codecs="vp8"'},
      {url: video.dataset.src, type: 'video/mp4'}
    ].filter(source => source.url && video.canPlayType(source.type)),
    next: 0,
    loaded: false,
    wantsPlay: false,
    failed: false
  }));

  function showFailure(index) {
    if (index !== active) return;
    const local = location.protocol === 'file:';
    status.textContent = isChinese
      ? (local ? '当前本地预览未能加载视频。请通过本地 HTTP 预览地址在 Edge 或 Chrome 中打开，视频可在页面内播放。'
        : '视频未能加载。请检查网络并刷新页面，或换用 Edge / Chrome 打开。')
      : (local ? 'This local preview could not load the video. Open the local HTTP preview in Edge or Chrome for inline playback.'
        : 'The video could not load. Check your connection and refresh, or open this page in Edge / Chrome.');
  }

  function loadNextFormat(index) {
    const state = media[index];
    const source = state.candidates[state.next++];
    if (!source) {
      state.failed = true;
      showFailure(index);
      return;
    }
    state.loaded = true;
    videos[index].src = source.url;
    videos[index].load();
  }

  function playActive() {
    const index = active;
    const video = videos[index];
    media[index].wantsPlay = true;
    if (media[index].failed) { showFailure(index); return; }
    const attempt = video.play();
    if (attempt && typeof attempt.then === 'function') {
      attempt.then(() => {
        if (active !== index || document.hidden || !inView) video.pause();
      }).catch(() => {
        // Browser autoplay settings are respected; the native play button remains usable.
      });
    }
  }

  function select(index, play = false) {
    const previous = active;
    active = (index + cards.length) % cards.length;
    const selected = cards[active];
    cards.forEach((card, i) => {
      const current = i === active;
      card.classList.toggle('is-active', current);
      card.classList.toggle('is-right', i === (active + 1) % cards.length);
      card.classList.toggle('is-left', i === (active + cards.length - 1) % cards.length);
      card.querySelector('[data-activate-video]').hidden = current;
      const video = videos[i];
      video.controls = current;
      video.tabIndex = current ? 0 : -1;
      video.setAttribute('aria-hidden', String(!current));
      if (!current) {
        media[i].wantsPlay = false;
        video.pause();
      }
    });
    selectors.forEach((button, i) => button.setAttribute('aria-pressed', String(i === active)));
    const video = videos[active];
    if ((previous !== active || video.ended) && video.readyState > 0) video.currentTime = 0;
    status.textContent = '';
    if (!media[active].loaded && !media[active].failed) loadNextFormat(active);
    root.querySelector('[data-video-title]').textContent = selected.dataset.title;
    root.querySelector('[data-video-target]').textContent = selected.dataset.target;
    root.querySelector('[data-video-meta]').textContent = selected.dataset.meta;
    root.querySelector('[data-video-counter]').textContent = `${String(active + 1).padStart(2, '0')} / 03`;
    const download = root.querySelector('[data-video-download]');
    download.href = video.dataset.src;
    download.setAttribute('download', video.dataset.src.split('/').pop());
    if (media[active].failed) {
      showFailure(active);
    } else if (play && !document.hidden) {
      inView = true;
      playActive();
    }
  }

  cards.forEach((card, i) => {
    card.querySelector('[data-activate-video]').addEventListener('click', () => {
      select(i, true);
      selectors[i].focus({preventScroll: true});
    });
    videos[i].muted = true;
    videos[i].loop = false;
    videos[i].addEventListener('play', () => {
      if (i !== active) videos[i].pause();
      else videos.forEach((video, j) => { if (i !== j) video.pause(); });
    });
    videos[i].addEventListener('error', () => {
      // Each local format is tried at most once; no repeated network retry loop.
      if (!media[i].failed) loadNextFormat(i);
    });
    videos[i].addEventListener('loadeddata', () => {
      if (i === active) status.textContent = '';
      if (i === active && media[i].wantsPlay && inView && !document.hidden) playActive();
    });
    videos[i].addEventListener('ended', () => {
      if (i === active && autoAdvance && inView && !document.hidden) select(active + 1, true);
    });
  });
  function updateAdvance() {
    if (!advanceButton) return;
    advanceButton.setAttribute('aria-pressed', String(autoAdvance));
    advanceButton.textContent = isChinese
      ? `播完自动切换：${autoAdvance ? '开' : '关'}`
      : `Auto-advance: ${autoAdvance ? 'on' : 'off'}`;
  }
  if (advanceButton) advanceButton.addEventListener('click', () => {
    autoAdvance = !autoAdvance;
    updateAdvance();
  });
  updateAdvance();
  selectors.forEach((button, i) => {
    button.addEventListener('click', () => select(i, true));
    button.addEventListener('keydown', event => {
      if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
      event.preventDefault();
      const index = event.key === 'Home' ? 0 : event.key === 'End' ? cards.length - 1 : i + (event.key === 'ArrowRight' ? 1 : -1);
      select(index, true);
      selectors[active].focus();
    });
  });
  root.querySelector('[data-video-prev]').addEventListener('click', () => select(active - 1, true));
  root.querySelector('[data-video-next]').addEventListener('click', () => select(active + 1, true));
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) videos.forEach(video => video.pause());
  });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      inView = entries[0].isIntersecting && entries[0].intersectionRatio >= 0.35;
      if (!inView) videos.forEach(video => video.pause());
      else if (!initialAutoplayAttempted && !reducedMotion.matches && !document.hidden) {
        initialAutoplayAttempted = true;
        playActive();
      }
    }, {threshold: [0, 0.35]});
    observer.observe(root.querySelector('.video-stage'));
  }
  select(0);
})();
