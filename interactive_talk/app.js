// Interactive refinement viewer.
// Tunable timings (ms). Edit freely; changes take effect on reload.
const CONFIG = {
  typeMs:          20,  // per-char typing delay (diff insert + rewrite type)
  deleteMs:      0.02,  // per-char forward-delete delay
  keepPauseMs:      0,  // pause after a kept segment (0 = instant skip)
  segmentPauseMs:  10,  // pause between diff ops
  rewritePauseMs: 100,  // gap between erase phase and type phase in rewrite mode
};

const beforeEl     = document.getElementById('before');
const afterEl      = document.getElementById('after');
const breadcrumbEl = document.getElementById('breadcrumb');
const figureEl     = document.getElementById('figure');

let tree       = null;
let currentId  = null;
let pathIds    = [];
let animating  = false;
let preorderIds  = [];    // flat list of ids in DFS preorder, for direction check
let lastFromText = null;  // for space-to-replay
let lastToText   = null;
let lastForward  = true;
let lastMode     = 'diff'; // 'diff' | 'rewrite' — for replay
let lastRanges   = [];     // highlight ranges for last rewrite replay
let skipRequested = false; // set by onKey during animation; collapses remaining ops
let queuedKey     = null;  // key to re-dispatch once current animation settles

async function init() {
  try {
    const resp = await fetch('tree.json', { cache: 'no-store' });
    tree = await resp.json();
  } catch (e) {
    beforeEl.textContent =
      "Serve locally: run `python -m http.server` in this folder, then open http://localhost:8000";
    return;
  }
  currentId = tree.id;
  pathIds   = [tree.id];
  computePreorder();
  const rootParsed = parseHighlights(tree.text);
  renderWithHighlights(beforeEl, rootParsed.clean, rootParsed.ranges);
  afterEl.textContent = '';
  updateFigure(tree);
  updateBreadcrumb();
  document.addEventListener('keydown', onKey);
}

function updateFigure(node) {
  if (node && node.figure) {
    const safe = String(node.figure).replace(/[&<>"']/g,
      c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const isImage = /\.(png|jpe?g|gif|webp|svg)$/i.test(node.figure);
    figureEl.innerHTML = isImage
      ? `<img class="figure-image" src="${safe}" alt="">`
      : `<div class="figure-placeholder">${safe}</div>`;
    figureEl.classList.add('visible');
  } else {
    figureEl.innerHTML = '';
    figureEl.classList.remove('visible');
  }
}

function computePreorder() {
  preorderIds = [];
  (function walk(n) {
    preorderIds.push(n.id);
    (n.children || []).forEach(walk);
  })(tree);
}

function isForward(fromId, toId) {
  return preorderIds.indexOf(toId) > preorderIds.indexOf(fromId);
}

// ----- tree helpers -----
function findNode(id, node = tree) {
  if (node.id === id) return node;
  for (const c of node.children || []) {
    const f = findNode(id, c);
    if (f) return f;
  }
  return null;
}

function findParent(id, node = tree, parent = null) {
  if (node.id === id) return parent;
  for (const c of node.children || []) {
    const f = findParent(id, c, node);
    if (f !== null) return f;
    if (c.id === id) return node;
  }
  return null;
}

// Preorder-DFS: "next" = first child, else nearest ancestor's next sibling.
function preorderNext(node) {
  if (node.children && node.children.length) return node.children[0];
  let cur = node;
  while (true) {
    const parent = findParent(cur.id);
    if (!parent) return null;
    const sibs = parent.children;
    const idx  = sibs.indexOf(cur);
    if (idx < sibs.length - 1) return sibs[idx + 1];
    cur = parent;
  }
}

// Preorder-DFS: "prev" = previous sibling's rightmost descendant, else parent.
function preorderPrev(node) {
  const parent = findParent(node.id);
  if (!parent) return null;
  const sibs = parent.children;
  const idx  = sibs.indexOf(node);
  if (idx === 0) return parent;
  let cur = sibs[idx - 1];
  while (cur.children && cur.children.length) cur = cur.children[cur.children.length - 1];
  return cur;
}

function rebuildPath() {
  const path = [];
  let n = currentId;
  while (n) {
    path.unshift(n);
    const p = findParent(n);
    n = p ? p.id : null;
  }
  pathIds = path;
}

function updateBreadcrumb() {
  breadcrumbEl.textContent = pathIds.join(' › ');
}

// ----- tokenize + LCS diff -----
function tokenize(text) {
  // Separate tokens for: word runs, punctuation runs, whitespace runs.
  // Keeps "word" stable when only surrounding punctuation changes (e.g. "word." → "word,").
  // Unicode letter/number classes so French accents tokenize cleanly.
  return text.match(/[\p{L}\p{N}'\-]+|[^\s\p{L}\p{N}'\-]+|\s+/gu) || [];
}

function diffTokens(a, b) {
  const n = a.length, m = b.length;
  const lcs = Array.from({ length: n + 1 }, () => new Int32Array(m + 1));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      if (a[i] === b[j]) lcs[i][j] = lcs[i + 1][j + 1] + 1;
      else lcs[i][j] = Math.max(lcs[i + 1][j], lcs[i][j + 1]);
    }
  }
  const ops = [];
  let i = 0, j = 0;
  const push = (type, text) => {
    const last = ops[ops.length - 1];
    if (last && last.type === type) last.text += text;
    else ops.push({ type, text });
  };
  while (i < n && j < m) {
    if (a[i] === b[j])                      { push('keep',   a[i]); i++; j++; }
    else if (lcs[i + 1][j] >= lcs[i][j + 1]) { push('delete', a[i]); i++; }
    else                                     { push('insert', b[j]); j++; }
  }
  while (i < n) push('delete', a[i++]);
  while (j < m) push('insert', b[j++]);
  return ops;
}

// ----- highlight markers -----
// Author syntax: wrap words/phrases in [[...]] inside a node's text field to
// force them into the .fresh class. Brackets are stripped for rendering; the
// spans they mark are used in rewrite mode (ignored in diff mode).
function parseHighlights(text) {
  const ranges = [];
  let clean = '';
  let i = 0;
  while (i < text.length) {
    if (text[i] === '[' && text[i + 1] === '[') {
      const close = text.indexOf(']]', i + 2);
      if (close === -1) { clean += text[i++]; continue; }
      const inner = text.slice(i + 2, close);
      const start = clean.length;
      clean += inner;
      ranges.push({ start, end: clean.length });
      i = close + 2;
    } else {
      clean += text[i++];
    }
  }
  return { clean, ranges };
}

// Render clean text into targetEl with hand-picked ranges wrapped in .fresh.
// Used for the root on load (no transition has happened yet).
function renderWithHighlights(targetEl, clean, ranges) {
  targetEl.replaceChildren();
  if (!ranges.length) { targetEl.textContent = clean; return; }
  const sorted = [...ranges].sort((a, b) => a.start - b.start);
  let cursor = 0;
  for (const { start, end } of sorted) {
    if (start > cursor) targetEl.appendChild(document.createTextNode(clean.slice(cursor, start)));
    const span = document.createElement('span');
    span.className = 'fresh';
    span.textContent = clean.slice(start, end);
    targetEl.appendChild(span);
    cursor = end;
  }
  if (cursor < clean.length) targetEl.appendChild(document.createTextNode(clean.slice(cursor)));
}

// ----- animation -----
const sleep = ms => new Promise(r => setTimeout(r, ms));

// Highlight only letter/number runs (including ' and - so contractions like
// "don't" stay intact); punctuation and whitespace render as plain text.
const WORDISH_RUN = /[\p{L}\p{N}'\-]+|[^\p{L}\p{N}'\-]+/gu;
const WORDISH_CHAR = /[\p{L}\p{N}'\-]/u;

function appendInsert(text, showFresh) {
  if (!showFresh) {
    beforeEl.appendChild(document.createTextNode(text));
    return;
  }
  const parts = text.match(WORDISH_RUN) || [];
  for (const part of parts) {
    if (WORDISH_CHAR.test(part)) {
      const span = document.createElement('span');
      span.className = 'fresh';
      span.textContent = part;
      beforeEl.appendChild(span);
    } else {
      beforeEl.appendChild(document.createTextNode(part));
    }
  }
}

async function animateTransition(fromText, toText, { showFresh = true } = {}) {
  animating = true;
  skipRequested = false;
  const ops = diffTokens(tokenize(fromText), tokenize(toText));

  // Reset: whole fromText in `after`, cursor at position 0.
  beforeEl.replaceChildren();
  afterEl.textContent = fromText;

  for (const op of ops) {
    if (op.type === 'keep') {
      // Move the kept chunk from after → before as a plain text node.
      const chunk = afterEl.textContent.slice(0, op.text.length);
      afterEl.textContent = afterEl.textContent.slice(op.text.length);
      beforeEl.appendChild(document.createTextNode(chunk));
      if (CONFIG.keepPauseMs && !skipRequested) await sleep(CONFIG.keepPauseMs);
    } else if (op.type === 'delete') {
      if (skipRequested) {
        afterEl.textContent = afterEl.textContent.slice(op.text.length);
      } else {
        for (let k = 0; k < op.text.length; k++) {
          if (skipRequested) {
            afterEl.textContent = afterEl.textContent.slice(op.text.length - k);
            break;
          }
          afterEl.textContent = afterEl.textContent.slice(1);
          await sleep(CONFIG.deleteMs);
        }
      }
    } else {
      if (skipRequested) {
        appendInsert(op.text, showFresh);
      } else {
        const chars = [...op.text];
        let i = 0;
        while (i < chars.length) {
          if (skipRequested) {
            appendInsert(chars.slice(i).join(''), showFresh);
            break;
          }
          appendInsert(chars[i++], showFresh);
          await sleep(CONFIG.typeMs);
        }
      }
    }
    if (CONFIG.segmentPauseMs && !skipRequested) await sleep(CONFIG.segmentPauseMs);
  }
  animating = false;
}

// Rewrite mode: fast-erase the current text, pause, then type out the new
// text with author-specified ranges rendered in .fresh. No diff is computed;
// this is for jumps where the LCS overlap between fromText and toText would
// be too noisy to read.
async function animateRewrite(fromText, toText, ranges) {
  animating = true;
  skipRequested = false;

  // Phase 1: fast-erase everything currently on stage.
  beforeEl.replaceChildren();
  afterEl.textContent = fromText;
  if (skipRequested) {
    afterEl.textContent = '';
  } else {
    const n = fromText.length;
    for (let k = 0; k < n; k++) {
      if (skipRequested) { afterEl.textContent = ''; break; }
      afterEl.textContent = afterEl.textContent.slice(1);
      await sleep(CONFIG.deleteMs);
    }
  }

  // Between-phase beat so the user registers "erased → now writing".
  if (CONFIG.rewritePauseMs && !skipRequested) await sleep(CONFIG.rewritePauseMs);

  // Phase 2: type toText char-by-char; chars inside a highlight range go into
  // a .fresh span (reused while we're still inside the same range).
  const chars = [...toText];
  const hl = new Array(chars.length).fill(false);
  for (const { start, end } of ranges) {
    for (let k = start; k < end && k < hl.length; k++) hl[k] = true;
  }
  let openSpan = null;
  const emit = (ch, isH) => {
    if (isH) {
      if (!openSpan) {
        openSpan = document.createElement('span');
        openSpan.className = 'fresh';
        beforeEl.appendChild(openSpan);
      }
      openSpan.appendChild(document.createTextNode(ch));
    } else {
      openSpan = null;
      beforeEl.appendChild(document.createTextNode(ch));
    }
  };
  for (let idx = 0; idx < chars.length; idx++) {
    if (skipRequested) {
      for (let k = idx; k < chars.length; k++) emit(chars[k], hl[k]);
      break;
    }
    emit(chars[idx], hl[idx]);
    await sleep(CONFIG.typeMs);
  }
  animating = false;
}

function currentText() {
  return beforeEl.textContent + afterEl.textContent;
}

async function goTo(node) {
  if (animating || !node) return;
  const fromText = currentText();
  const forward  = isForward(currentId, node.id);
  const { clean, ranges } = parseHighlights(node.text);
  const mode = node.mode === 'rewrite' ? 'rewrite' : 'diff';
  updateFigure(node);                       // shift layout first, then animate
  if (mode === 'rewrite') {
    await animateRewrite(fromText, clean, ranges);
  } else {
    await animateTransition(fromText, clean, { showFresh: forward });
  }
  lastFromText = fromText;
  lastToText   = clean;
  lastForward  = forward;
  lastMode     = mode;
  lastRanges   = ranges;
  currentId    = node.id;
  rebuildPath();
  updateBreadcrumb();
  flushQueued();
}

async function replayLast() {
  if (animating || lastFromText === null) return;
  animating = true;
  beforeEl.replaceChildren();
  beforeEl.textContent = lastFromText;
  afterEl.textContent  = '';
  animating = false;
  if (lastMode === 'rewrite') {
    await animateRewrite(lastFromText, lastToText, lastRanges);
  } else {
    await animateTransition(lastFromText, lastToText, { showFresh: lastForward });
  }
  flushQueued();
}

function flushQueued() {
  if (!queuedKey) return;
  const k = queuedKey;
  queuedKey = null;
  performKey(k);
}

// ----- keyboard nav -----
const HANDLED_KEYS = new Set(['ArrowRight','ArrowLeft','ArrowUp','ArrowDown',' ','r','R']);

function onKey(e) {
  if (!HANDLED_KEYS.has(e.key)) return;
  if (e.key === ' ') e.preventDefault();

  if (animating) {
    // Second-press behaviour: collapse current animation immediately and
    // queue this key so it fires as soon as the animation settles.
    skipRequested = true;
    queuedKey = e.key;
    return;
  }
  performKey(e.key);
}

function performKey(key) {
  const node   = findNode(currentId);
  const parent = findParent(currentId);

  if (key === 'ArrowRight') {
    goTo(preorderNext(node));
  } else if (key === 'ArrowLeft') {
    goTo(preorderPrev(node));
  } else if (key === 'ArrowDown' || key === 'ArrowUp') {
    if (!parent) return;
    const sibs  = parent.children;
    const idx   = sibs.findIndex(s => s.id === currentId);
    const delta = key === 'ArrowDown' ? 1 : -1;
    goTo(sibs[(idx + delta + sibs.length) % sibs.length]);
  } else if (key === ' ') {
    replayLast();
  } else if (key === 'r' || key === 'R') {
    goTo(tree);
  }
}

init();
