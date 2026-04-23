// Interactive refinement viewer.
// Tunable timings (ms). Edit freely; changes take effect on reload.
const CONFIG = {
  typeMs:           12,  // per-char typing delay (diff insert + rewrite type)
  deleteMs:       0.02,  // per-char forward-delete delay
  keepPauseMs:       0,  // pause after a kept segment (0 = instant skip)
  segmentPauseMs:    6,  // pause between diff ops
  rewriteFadeMs:   100,  // text rewrite phase-1 fade-out + SVG layer fade
  rewritePauseMs:   50,  // gap between fade-out and type phase in rewrite mode
  figureFadeInMs: 1000,  // figure panel fade-in (first render + swap)
  figureFadeOutMs: 150,  // figure panel fade-out (swap + going to no-figure)
};

const beforeEl     = document.getElementById('before');
const afterEl      = document.getElementById('after');
const breadcrumbEl = document.getElementById('breadcrumb');
const figureEl     = document.getElementById('figure');
let   minimapEl    = null;  // injected by setupMinimap on init
let   minimapLayout = null; // { positions: Map<id, {x,y,structural,parentId}>, width, height }

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

// Figure state. The panel may hold one of: nothing, a static image, an
// inline SVG (whose .layer groups get toggled), or a text placeholder.
// `figureToken` guards against stale async swaps superseding a newer update.
let currentFigureSrc  = null;
let currentFigureType = null; // 'static' | 'svg' | 'placeholder' | null
let figureToken       = 0;

// tree.json keeps authoring flat (separate `nodes` map + id-only `tree` outline);
// reifyTree inflates that into the nested shape the rest of the code walks.
function reifyTree(data) {
  const nodes   = (data && data.nodes) || {};
  const outline = (data && data.tree)  || {};
  const rootId  = data && data.root;
  if (!rootId) {
    console.error('tree.json: missing "root" field');
    return { id: '(missing root)', text: 'tree.json: missing "root" field', children: [] };
  }
  function build(id, subtree) {
    const raw = nodes[id];
    if (!raw) console.warn(`tree.json: node "${id}" referenced in tree but not in nodes map`);
    const node = {
      id,
      text: (raw && raw.text) || '',
      children: Object.keys(subtree || {}).map(cid => build(cid, subtree[cid])),
    };
    if (raw && raw.mode   !== undefined) node.mode   = raw.mode;
    if (raw && raw.figure !== undefined) node.figure = raw.figure;
    return node;
  }
  return build(rootId, outline[rootId] || {});
}

async function init() {
  let data;
  try {
    const resp = await fetch('tree.json', { cache: 'no-store' });
    data = await resp.json();
  } catch (e) {
    beforeEl.textContent =
      "Serve locally: run `python -m http.server` in this folder, then open http://localhost:8000";
    return;
  }
  tree = reifyTree(data);
  currentId = tree.id;
  pathIds   = [tree.id];
  computePreorder();
  setupMinimap(data);
  // Sync CSS fade durations with CONFIG so tuning in one place propagates.
  // Panel fade-in drives the .figure.visible CSS animation; fade-out is set
  // inline on the element's transitionDuration just before each opacity flip.
  figureEl.style.setProperty('--layer-fade-ms',    CONFIG.rewriteFadeMs    + 'ms');
  figureEl.style.setProperty('--panel-fade-in-ms', CONFIG.figureFadeInMs   + 'ms');
  const rootParsed = parseHighlights(tree.text);
  renderWithHighlights(beforeEl, rootParsed.clean, rootParsed.ranges);
  afterEl.textContent = '';
  updateFigure(tree);
  updateBreadcrumb();
  updateMinimap();
  document.addEventListener('keydown', onKey);
}

function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g,
    c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// Normalize a node's `figure` field (string | object | missing) into a spec
// the updater can dispatch on. Keeps the dispatch logic below straightforward.
function parseFigureSpec(node) {
  if (!node || node.figure == null) return null;
  if (typeof node.figure === 'string') {
    const isImage = /\.(png|jpe?g|gif|webp|svg)$/i.test(node.figure);
    return isImage
      ? { type: 'static',      src: node.figure }
      : { type: 'placeholder', text: node.figure };
  }
  if (typeof node.figure === 'object' && node.figure.svg) {
    return { type: 'svg', src: node.figure.svg, show: node.figure.show || [] };
  }
  return null;
}

// Toggle .layer-visible on each SVG .layer based on the show set. CSS handles
// the opacity fade. Absolute, not cumulative — the set fully determines state.
function applyShowList(show) {
  const wanted = new Set(show);
  figureEl.querySelectorAll('.layer').forEach(layer => {
    layer.classList.toggle('layer-visible', wanted.has(layer.id));
  });
}

// Fire-and-forget from goTo — runs in parallel with the text animation. When
// the target is the same SVG, we only re-apply the show list (CSS transitions
// handle per-layer fade). When it's a different figure (or swapping to/from
// empty), we fade the whole panel, load the new content, fade back in.
async function updateFigure(node) {
  const spec  = parseFigureSpec(node);
  const token = ++figureToken;

  if (!spec) {
    if (currentFigureType !== null) {
      figureEl.style.transitionDuration = CONFIG.figureFadeOutMs + 'ms';
      figureEl.style.opacity = '0';
      await sleep(CONFIG.figureFadeOutMs);
      if (token !== figureToken) return;
    }
    figureEl.classList.remove('visible');
    figureEl.style.opacity = '';
    figureEl.replaceChildren();
    currentFigureSrc  = null;
    currentFigureType = null;
    return;
  }

  // Same inline SVG, just a different layer selection → CSS layer fade only.
  if (spec.type === 'svg'
      && currentFigureType === 'svg'
      && spec.src === currentFigureSrc) {
    applyShowList(spec.show);
    return;
  }

  // Fade out what's there. First-render (wasVisible=false) has nothing to fade
  // — the CSS animation on .figure.visible handles the fade-in in that case.
  const wasVisible = currentFigureType !== null;
  if (wasVisible) {
    figureEl.style.transitionDuration = CONFIG.figureFadeOutMs + 'ms';
    figureEl.style.opacity = '0';
    await sleep(CONFIG.figureFadeOutMs);
    if (token !== figureToken) return;
  }

  if (spec.type === 'svg') {
    let txt;
    try {
      const resp = await fetch(spec.src, { cache: 'no-store' });
      txt = await resp.text();
    } catch (e) {
      figureEl.innerHTML = `<div class="figure-placeholder">${escapeHtml(spec.src)}</div>`;
      figureEl.classList.add('visible');
      figureEl.style.transitionDuration = CONFIG.figureFadeInMs + 'ms';
      figureEl.style.opacity = '1';
      currentFigureSrc  = spec.src;
      currentFigureType = 'placeholder';
      return;
    }
    if (token !== figureToken) return;
    figureEl.innerHTML = txt;
    applyShowList(spec.show);
  } else if (spec.type === 'static') {
    figureEl.innerHTML = `<img class="figure-image" src="${escapeHtml(spec.src)}" alt="">`;
  } else {
    figureEl.innerHTML = `<div class="figure-placeholder">${escapeHtml(spec.text)}</div>`;
  }

  figureEl.classList.add('visible');
  figureEl.style.transitionDuration = CONFIG.figureFadeInMs + 'ms';
  figureEl.style.opacity = '1';
  currentFigureSrc  = spec.src || spec.text || null;
  currentFigureType = spec.type;
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

  // Phase 1: fade the existing stage to 0, then clear it. Much calmer than
  // char-by-char erasing on long text, and the erasure carries no meaning —
  // only the arrival of the new text does.
  if (CONFIG.rewriteFadeMs && !skipRequested) {
    beforeEl.style.opacity = '0';
    afterEl.style.opacity  = '0';
    await sleep(CONFIG.rewriteFadeMs);
  }
  beforeEl.replaceChildren();
  afterEl.textContent = '';
  beforeEl.style.opacity = '';
  afterEl.style.opacity  = '';

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

  // Commit state eagerly so minimap cursor (and breadcrumb) lead the text
  // animation — navigation feedback is instant even while text is still typing.
  lastFromText = fromText;
  lastToText   = clean;
  lastForward  = forward;
  lastMode     = mode;
  lastRanges   = ranges;
  currentId    = node.id;
  rebuildPath();
  updateBreadcrumb();
  updateMinimap();
  updateFigure(node);                       // shifts layout, then animates

  if (mode === 'rewrite') {
    await animateRewrite(fromText, clean, ranges);
  } else {
    await animateTransition(fromText, clean, { showFresh: forward });
  }
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
}

// ----- keyboard nav -----
const HANDLED_KEYS = new Set(['ArrowRight','ArrowLeft','ArrowUp','ArrowDown',' ','r','R']);

function onKey(e) {
  if (!HANDLED_KEYS.has(e.key)) return;
  if (e.key === ' ') e.preventDefault();

  if (animating) {
    // Second-press behaviour: collapse the current animation to its final
    // state. The key is *not* queued — the user must press again to navigate.
    skipRequested = true;
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

// ===================================================================
// MINIMAP — stylized tips-only tree above the breadcrumb.
// Only nodes listed in data.tips render as dots; content chains
// between tips collapse into edges whose length is proportional to
// the count of "meaningful" (rewrite-mode, non-layer-reveal) content
// nodes between them.
//
// Cursor = closest tip ancestor of the currentId. Navigating among
// content nodes that share a tip ancestor leaves the minimap cursor
// on that tip (a finer in-branch cursor can be added later).
// ===================================================================

// A content node is "countable" if it represents a distinct step in
// the talk: rewrite-mode. Diff-mode (iterative text extensions of a
// rewrite node) are skipped. Note: we don't filter same-SVG siblings —
// sClust1→sClust4 etc. share an SVG via layer toggles but still do
// full text rewrites, so they count as real steps.
function countsAsContent(node, _parent) {
  return node.mode === 'rewrite';
}

function closestTipAncestor(id, tipsSet) {
  let cur = id;
  while (cur) {
    if (tipsSet.has(cur)) return cur;
    const p = findParent(cur);
    cur = p ? p.id : null;
  }
  return null;
}

function computeTipsSet(data) {
  if (data && Array.isArray(data.tips) && data.tips.length) {
    return new Set(data.tips);
  }
  return new Set([tree.id]);  // fallback: just root
}

// Count of countable content nodes inside a tip's sub-tree that are NOT
// inside any descendant tip's sub-tree. For leaf tips, this is the full
// "trailing chapter depth"; for non-leaf tips, it's side content orphaned
// under this tip (rendered separately, if at all).
function countTrailingContent(tipId, tipsSet) {
  const tipNode = findNode(tipId);
  if (!tipNode) return 0;
  let count = 0;
  (function dfs(node) {
    for (const c of node.children || []) {
      if (tipsSet.has(c.id)) continue;  // stop at descendant tips
      if (countsAsContent(c, node)) count++;
      dfs(c);
    }
  })(tipNode);
  return count;
}

function computeMinimapLayout(tipsSet) {
  // tipInfo[tipId] = { parentTipId, contentFromParent, childTipIds: [], trailingContent }
  const tipInfo = new Map();
  let rootTipId = null;

  (function walk(node, parent, parentTipId, pathContent) {
    if (tipsSet.has(node.id)) {
      tipInfo.set(node.id, {
        parentTipId,
        contentFromParent: pathContent,
        childTipIds: [],
        trailingContent: 0,
      });
      if (parentTipId === null) rootTipId = node.id;
      else tipInfo.get(parentTipId).childTipIds.push(node.id);
      parentTipId = node.id;
      pathContent = 0;
    } else if (countsAsContent(node, parent)) {
      pathContent++;
    }
    for (const c of node.children || []) walk(c, node, parentTipId, pathContent);
  })(tree, null, null, 0);

  if (!rootTipId) return { positions: new Map(), width: 40, height: 20 };

  for (const [tipId, info] of tipInfo) {
    info.trailingContent = countTrailingContent(tipId, tipsSet);
  }

  // Lane assignment on the tips-only tree: first child-tip inherits
  // parent's lane; siblings 2+ take new lanes.
  let nextLane = 1;
  const tipLane = new Map();
  (function lay(tipId, inherited) {
    tipLane.set(tipId, inherited);
    tipInfo.get(tipId).childTipIds.forEach((c, i) => {
      lay(c, (i === 0) ? inherited : nextLane++);
    });
  })(rootTipId, 0);
  const laneCount = nextLane;

  // X = cumulative content-distance from root along the tips path.
  // MIN_EDGE guarantees even zero-content edges show as a visible link.
  // Bump COLW if you want the branches stretched out more; CSS width
  // on #minimap then scales the whole SVG to pixel target.
  const MIN_EDGE = 1;
  const COLW = 22;
  const tipX = new Map();
  (function placeX(tipId, baseX) {
    tipX.set(tipId, baseX);
    tipInfo.get(tipId).childTipIds.forEach(c => {
      const edgeLen = Math.max(MIN_EDGE, tipInfo.get(c).contentFromParent);
      placeX(c, baseX + edgeLen * COLW);
    });
  })(rootTipId, 0);

  const padX = 12;
  const padY = 8;
  const laneH = 7;

  // Width includes trailing-chain extensions from leaf tips.
  let maxExtent = 0;
  for (const [tipId, info] of tipInfo) {
    const isLeaf = info.childTipIds.length === 0;
    const trailLen = isLeaf ? info.trailingContent * COLW : 0;
    maxExtent = Math.max(maxExtent, tipX.get(tipId) + trailLen);
  }
  const width  = padX * 2 + maxExtent;
  const height = padY * 2 + Math.max(0, laneCount - 1) * laneH;

  // subtree size per tip — used to position the in-branch cursor as a
  // fraction along the trail (every preorder step = one slot).
  const subtreeSize = new Map();
  (function measure(tipId) {
    const node = findNode(tipId);
    let count = 0;
    (function w(n) { count++; for (const c of n.children || []) w(c); })(node);
    subtreeSize.set(tipId, count);
    for (const c of tipInfo.get(tipId).childTipIds) measure(c);
  })(rootTipId);

  const positions = new Map();
  for (const [tipId, info] of tipInfo) {
    const isLeaf = info.childTipIds.length === 0;
    positions.set(tipId, {
      x: padX + tipX.get(tipId),
      y: padY + tipLane.get(tipId) * laneH,
      parentTipId: info.parentTipId,
      contentFromParent: info.contentFromParent,
      trailingContent: info.trailingContent,
      isLeaf,
      trailLen: isLeaf ? info.trailingContent * COLW : 0,
      subtreeSize: subtreeSize.get(tipId),
    });
  }
  return { positions, width, height, tipsSet };
}

function setupMinimap(data) {
  minimapEl = document.getElementById('minimap');
  if (!minimapEl) {
    minimapEl = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    minimapEl.setAttribute('id', 'minimap');
    document.body.appendChild(minimapEl);
  }

  const tipsSet = computeTipsSet(data);
  minimapLayout = computeMinimapLayout(tipsSet);
  const { positions, width, height } = minimapLayout;

  minimapEl.setAttribute('viewBox', `0 0 ${width} ${height}`);
  minimapEl.setAttribute('width', width);
  minimapEl.setAttribute('height', height);
  minimapEl.replaceChildren();

  // Inter-tip edges first (drawn under nodes).
  for (const [id, p] of positions) {
    if (!p.parentTipId) continue;
    const pp = positions.get(p.parentTipId);
    if (!pp) continue;
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', pp.x);
    line.setAttribute('y1', pp.y);
    line.setAttribute('x2', p.x);
    line.setAttribute('y2', p.y);
    line.setAttribute('class', 'mm-edge');
    line.setAttribute('data-target', id);
    minimapEl.appendChild(line);
  }

  // Trailing chains on leaf tips — length ∝ downstream content.
  // Each trail has a dim base and an amber progress overlay that
  // grows as the user navigates through the chapter's content.
  for (const [id, p] of positions) {
    if (!p.isLeaf || p.trailLen <= 0) continue;
    const trail = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    trail.setAttribute('x1', p.x);
    trail.setAttribute('y1', p.y);
    trail.setAttribute('x2', p.x + p.trailLen);
    trail.setAttribute('y2', p.y);
    trail.setAttribute('class', 'mm-trail');
    trail.setAttribute('data-tip', id);
    minimapEl.appendChild(trail);

    const progress = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    progress.setAttribute('x1', p.x);
    progress.setAttribute('y1', p.y);
    progress.setAttribute('x2', p.x);  // zero-length until a navigation sets it
    progress.setAttribute('y2', p.y);
    progress.setAttribute('class', 'mm-trail-progress');
    progress.setAttribute('data-tip', id);
    minimapEl.appendChild(progress);
  }

  // Tip dots.
  for (const [id, p] of positions) {
    const c = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    c.setAttribute('cx', p.x);
    c.setAttribute('cy', p.y);
    c.setAttribute('r', 2.8);
    c.setAttribute('class', 'mm-node mm-struct');
    c.setAttribute('data-id', id);
    c.addEventListener('click', () => {
      if (animating) return;
      const node = findNode(id);
      if (node) goTo(node);
    });
    minimapEl.appendChild(c);
  }
}

function updateMinimap() {
  if (!minimapEl || !minimapLayout) return;
  const { tipsSet, positions } = minimapLayout;
  const currentTipId = closestTipAncestor(currentId, tipsSet);

  // Walk up the tips tree from currentTipId to collect the highlighted path.
  const tipPath = new Set();
  for (let t = currentTipId; t; ) {
    tipPath.add(t);
    const info = positions.get(t);
    t = info ? info.parentTipId : null;
  }

  minimapEl.querySelectorAll('.mm-node').forEach(el => {
    const id = el.getAttribute('data-id');
    el.classList.toggle('mm-current', id === currentTipId);
    el.classList.toggle('mm-path',    tipPath.has(id));
  });
  minimapEl.querySelectorAll('.mm-edge').forEach(el => {
    const targetId = el.getAttribute('data-target');
    el.classList.toggle('mm-edge-path', tipPath.has(targetId));
  });
  minimapEl.querySelectorAll('.mm-trail').forEach(el => {
    const tipId = el.getAttribute('data-tip');
    el.classList.toggle('mm-trail-active', tipId === currentTipId);
  });

  // In-branch cursor: extend the progress overlay from the current tip
  // to a position along its trail. Step = DFS-preorder index within the
  // tip's sub-tree, normalized to [0, 1]. Non-leaf tips have no trail —
  // cursor stays on the tip dot (progress x2 held at tip.x).
  const curTip = positions.get(currentTipId);
  const curPos = preorderIds.indexOf(currentId);
  const tipPos = currentTipId ? preorderIds.indexOf(currentTipId) : -1;
  minimapEl.querySelectorAll('.mm-trail-progress').forEach(el => {
    const tipId = el.getAttribute('data-tip');
    const p = positions.get(tipId);
    let x2 = p.x;
    if (tipId === currentTipId && curTip && curTip.isLeaf && curTip.trailLen > 0) {
      const denom = Math.max(1, curTip.subtreeSize - 1);
      const frac = Math.max(0, Math.min(1, (curPos - tipPos) / denom));
      x2 = p.x + frac * p.trailLen;
    }
    el.setAttribute('x2', x2);
  });
}

init();
