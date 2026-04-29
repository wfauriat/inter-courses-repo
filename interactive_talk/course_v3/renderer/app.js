'use strict';

const FADE_MS = 180;
const params = new URLSearchParams(location.search);
const compositionName = params.get('composition') || 'talk_30min_general';

const slideEl = document.getElementById('slide');
const titleEl = document.getElementById('slide-title');
const bodyEl = document.getElementById('slide-body');
const counterEl = document.getElementById('slide-counter');
const beatEl = document.getElementById('beat-name');
const badgesEl = document.getElementById('badges');
const progressEl = document.getElementById('progress-bar');
const helpEl = document.getElementById('help');

let comp = null;
let slides = [];
let currentIndex = 0;
let currentFace = null;  // null = use slide's default_face; else 'general' | 'technical'

async function init() {
  try {
    const resp = await fetch(`compositions/${compositionName}.json`,
                             { cache: 'no-store' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    comp = await resp.json();
  } catch (err) {
    titleEl.textContent = 'composition load failed';
    bodyEl.innerHTML = `<p>Could not load <code>compositions/${compositionName}.json</code>.</p>` +
                       `<p>Run <code>python3 composer.py configs/${compositionName}.yaml</code>` +
                       ` then serve from <code>course_v3/renderer/</code>.</p>` +
                       `<p>Error: ${err.message}</p>`;
    return;
  }
  slides = comp.slides || [];
  if (slides.length === 0) {
    titleEl.textContent = 'empty composition';
    return;
  }
  // URL hash for direct slide jump
  const hash = location.hash.match(/^#slide-(\d+)$/);
  if (hash) currentIndex = clamp(parseInt(hash[1], 10) - 1, 0, slides.length - 1);
  render(false);
  document.addEventListener('keydown', onKey);
  window.addEventListener('hashchange', onHash);
  helpEl.addEventListener('click', (e) => {
    if (e.target === helpEl) helpEl.hidden = true;
  });
}

function clamp(n, lo, hi) { return Math.max(lo, Math.min(hi, n)); }

function pickBody(slide) {
  const fh = slide.faces_html || {};
  const desired = currentFace || slide.default_face || 'general';
  return fh[desired] || fh.general || fh.technical || slide.body_html;
}

function render(animate = true) {
  const slide = slides[currentIndex];
  if (!slide) return;
  const apply = () => {
    titleEl.textContent = slide.title.toLowerCase();
    bodyEl.innerHTML = pickBody(slide);
    counterEl.textContent = `${currentIndex + 1} / ${slides.length}`;
    beatEl.textContent = beatLabel(slide);
    renderBadges(slide);
    progressEl.style.width = `${((currentIndex + 1) / slides.length) * 100}%`;
    location.hash = `slide-${currentIndex + 1}`;
    slideEl.classList.remove('fading');
    if (window.renderMathInElement) {
      window.renderMathInElement(bodyEl, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false },
          { left: '\\[', right: '\\]', display: true },
        ],
        throwOnError: false,
      });
    }
  };
  if (!animate) { apply(); return; }
  slideEl.classList.add('fading');
  setTimeout(apply, FADE_MS);
}

function beatLabel(slide) {
  // Find the spine card this slide is part of (its anchor)
  // Walk backwards from current slide until we hit a spine/hook
  for (let i = currentIndex; i >= 0; i--) {
    const s = slides[i];
    if (s.role === 'spine' || s.role === 'hook') {
      return s.title.toLowerCase();
    }
  }
  return '';
}

function renderBadges(slide) {
  const parts = [];
  const faceShown = (currentFace || slide.default_face || 'general');
  const faces = Object.keys(slide.faces_html || {});
  if (faces.length > 1) {
    parts.push(`<span class="badge face">${faceShown}</span>`);
  }
  if (slide.technical) parts.push('<span class="badge tech">technical</span>');
  if (slide.id === 'alignment_thesis') parts.push('<span class="badge thesis">thesis</span>');
  badgesEl.innerHTML = parts.join('');
}

function onKey(e) {
  if (helpEl.hidden === false &&
      e.key !== '?' && e.key !== 'h' && e.key !== 'H' && e.key !== 'Escape') return;
  switch (e.key) {
    case 'ArrowRight':
    case ' ':
    case 'PageDown':
      e.preventDefault();
      step(1);
      break;
    case 'ArrowLeft':
    case 'p':
    case 'PageUp':
      e.preventDefault();
      step(-1);
      break;
    case 'ArrowDown':
    case 'n':
      e.preventDefault();
      jumpChapter(1);
      break;
    case 'ArrowUp':
    case 'b':
      e.preventDefault();
      jumpChapter(-1);
      break;
    case 'Home':
    case 'g':
      currentIndex = 0;
      render();
      break;
    case 'End':
      currentIndex = slides.length - 1;
      render();
      break;
    case 't':
    case 'T':
      currentFace = (currentFace === 'technical') ? 'general' : 'technical';
      render(false);
      break;
    case 'f':
    case 'F':
      toggleFullscreen();
      break;
    case 'h':
    case 'H':
    case '?':
      helpEl.hidden = !helpEl.hidden;
      break;
    case 'Escape':
      helpEl.hidden = true;
      break;
  }
}

function step(delta) {
  const next = clamp(currentIndex + delta, 0, slides.length - 1);
  if (next !== currentIndex) {
    currentIndex = next;
    render();
  }
}

function jumpChapter(delta) {
  if (delta > 0) {
    for (let i = currentIndex + 1; i < slides.length; i++) {
      if (slides[i].role === 'spine' || slides[i].role === 'hook') {
        currentIndex = i; render(); return;
      }
    }
    currentIndex = slides.length - 1;
  } else {
    for (let i = currentIndex - 1; i >= 0; i--) {
      if (slides[i].role === 'spine' || slides[i].role === 'hook') {
        currentIndex = i; render(); return;
      }
    }
    currentIndex = 0;
  }
  render();
}

function toggleFullscreen() {
  if (!document.fullscreenElement) {
    document.documentElement.requestFullscreen?.();
  } else {
    document.exitFullscreen?.();
  }
}

function onHash() {
  const m = location.hash.match(/^#slide-(\d+)$/);
  if (!m) return;
  const i = clamp(parseInt(m[1], 10) - 1, 0, slides.length - 1);
  if (i !== currentIndex) {
    currentIndex = i;
    render();
  }
}

init();
