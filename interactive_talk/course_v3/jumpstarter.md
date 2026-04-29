# course_v3 — jumpstarter

A spec-native rebuild of the LLM-mechanism talk. Authored from
`../pedagogical-architecture-specs-v2.md` down, with the v1 build at
`../interactive_talk/` taken as *idea-source only* (not text-source).
v2 (`../course_v2/`) was a port-of-v1; v3 is a fresh authoring.

What this is **not**:

- A line-by-line port of v1 (that was v2; it had rendering issues
  because the v1 text was tuned for a typing-into-being viewer, not
  a slide deck).
- A rebuild of the v1 viewer. v3 ships its own slide-deck renderer.

What this **is**:

- A card library of **25 atomic cards**, each authored fresh, with
  two faces: `general` and `technical`.
- A composer that emits a flat slide list (no tree.json shape, no
  staging, no figure machinery).
- A minimal slide-deck renderer in `renderer/` (HTML + CSS + JS;
  ~200 LOC total). Dark mode, system fonts, keyboard nav.
- Three configs: 30-min general talk, 5-min pitch, 60-min technical.

## Files

```
course_v3/
|-- thesis.md              # locked thesis + alternates
|-- friction_map.md        # 2 audience profiles (general, technical)
|-- belief_trajectory.md   # 6 spine waypoints
|-- jumpstarter.md         # this file
|-- composer.py            # cards + config -> slide JSON
|-- cards/                 # 25 atomic cards
|-- configs/               # 3 format configs
|-- compositions/          # generated slide JSONs
|-- renderer/
|   |-- index.html, style.css, app.js  (~250 LOC total)
|   `-- compositions -> ../compositions  (symlink)
`-- review_passes/         # post-composition annotations
```

## Quick start

```bash
cd course_v3

# Generate compositions
python3 composer.py configs/talk_30min_general.yaml
python3 composer.py configs/pitch_5min_general.yaml
python3 composer.py configs/talk_60min_technical.yaml

# Run the slide deck
cd renderer
python3 -m http.server 8766
# open http://localhost:8766/?composition=talk_30min_general
```

Keyboard in the deck:

| key | action |
|---|---|
| → space | next slide |
| ← p | previous slide |
| ↓ | next chapter (next spine card) |
| ↑ | previous chapter |
| home / 0 | first slide |
| end | last slide |
| t | toggle technical-only filter |
| f | fullscreen |
| ? | help overlay |

## Card schema

Each card lives at `cards/<id>.md`. Frontmatter:

```yaml
---
id: <matches filename>
role: spine | branch | example | hook
thesis_role: load_bearing | enriching
prerequisites: [<card_id>, ...]
technical: true              # optional; hides unless include_technical
time_cost:
  short: <s>
  standard: <s>
  deep: <s>
faces:
  general: |
    Markdown content for the general/layman audience.
  technical: |
    Markdown content for the technical audience (formal idiom OK).
notes_to_self: |
  Authoring intent.
---

# <id>

(Markdown body — author commentary, not displayed.)
```

**Faces:** authored on **all** spine cards; on branches, just the
relevant face (often only `general`, sometimes only `technical`).

**Body of the card file** (the part below the closing `---`) is for
author commentary. The renderer never sees it.

## Composer behaviour

Reads `cards/*.md` + a config; emits `compositions/<format>.json`.

For each card in DFS order of the config's `tree`:
- Filter out technical cards if `include_technical: false`.
- Pick the face matching the config's `audience` (fallback to
  `general`).
- Render the markdown to HTML.
- Emit one slide entry.

Soft validations (warning, not failure):
- Every load-bearing card present (skipping technical cards if
  excluded).
- Prerequisites appear before dependents.
- Last spine card is `alignment_thesis`.
- Total `time_cost` within ~120% of `budget_seconds`.

## Renderer

Plain HTML + CSS + JS. No build step, no framework, no dependencies.
Dark mode by default. System fonts (serif body, sans headings,
monospace code). Keyboard-driven navigation.

The slide JSON is loaded once on page load; all slides are kept in
memory; navigation just updates which is rendered. Smooth fade
between slides (180ms).

## Spec compliance (v2 spec)

| Spec requirement | Where |
|---|---|
| One thesis sentence pinned | `thesis.md` |
| Spine of 5-7 beats | `belief_trajectory.md`; cards with `role: spine` |
| Friction map per audience | `friction_map.md` |
| Belief trajectory per load-bearing claim | `belief_trajectory.md` |
| Atomic cards with metadata + faces | `cards/*.md` |
| Authoring → composition → rendering separation | `composer.py` + `renderer/` |
| Two compositions before generalising | 30-min + 5-min generated |
| Review pass for resistance + rhythm | `review_passes/` |

What is *deliberately not* in the schema:

- Per-card persuasive metadata — handled at global level via
  `friction_map.md` (spec §1.4 explicitly).
- Per-card affective metadata — handled in `review_passes/` after
  composition.

## What changed from v2 (and why)

| Aspect | v2 | v3 |
|---|---|---|
| Card content | ported from v1 tree.json | authored fresh |
| Card count | 41 | 25 |
| Faces | layman / cs / math | general / technical |
| Stages | yes (for the v1 typing viewer) | no |
| Figures | layered SVGs from v1 | none |
| Renderer | adapted v1 JS viewer | bespoke slide deck |
| Composer output | tree.json shape | flat slide list |

Why:

- **Authoring fresh.** v1 text was calibrated for the typing-into-
  being viewer's pacing — short text per node, refinement-chain
  shape. Lifting that into v2 produced overly-long slides because
  what worked as a 4-stage typing animation crammed into one slide.
  v3's text is calibrated for slides directly.
- **Fewer cards.** v2 had cards-per-stage; v3 has cards-per-claim.
  ~25 cards is enough for a 30-min talk.
- **Two faces.** For "what is an LLM," cs and math cluster tightly;
  three faces was authoring drain without payoff. Split if a future
  rendering shows divergence.
- **No stages.** Stages were a v1-viewer concession. Slide decks
  don't need them.
- **No figures.** Per build constraint — too tightly coupled to v1's
  layered-SVG generators. A future iteration can add figures back as
  static images per slide.
- **Bespoke renderer.** ~250 LOC HTML/CSS/JS. Easier to evolve than
  the v1 viewer's ~1200 LOC of typing engine + minimap.

## Adding new content

1. Pick id, role, thesis_role, prerequisites.
2. Author both faces (or just one if branch).
3. Add to relevant config's `tree` field.
4. Run composer; check warnings + slide count.
5. Open the deck and step through.

## Where to look for deeper context

- `../pedagogical-architecture-specs-v2.md` — the spec.
- `../interactive_talk/` — v1 (idea-source only).
- `../course_v2/` — v2 (port-of-v1; superseded by v3).
- `thesis.md` / `friction_map.md` / `belief_trajectory.md` — the
  three living prose artifacts. Update after each rendering.

## Known limitations

- **No figures yet.** All visual anchoring is in text. The "embedding
  clusters" and "bank disambiguation" cards rely on textual
  description. If a future audience wants figures, add a `figure:`
  field to the relevant cards and an image renderer to the slide
  deck.
- **60-min technical config is short.** At deep depth it sums to
  ~30 min. The cards' `time_cost` values are slide-display times,
  not lecture times — a speaker would dwell 1.5-2x longer per slide
  in a real 60-min delivery. The composer's budget warning treats
  this as "well under budget" but it is not pathological; it is just
  a reminder that delivery time is not slide time.
- **No reflexive close as a separate card.** The reflexive line is
  an inline aside on the alignment_thesis technical face.
- **Beat numbering in slide JSON is naive** — every spine card
  increments the beat counter, including closers (ntp_summary
  becomes "beat 3" rather than the closer of beat 2). The renderer
  uses chapter labels (last spine card title) instead of beat
  numbers, so this is cosmetic.

## Invariants

- **v1 (`interactive_talk/`) is untouched.** Idea-source only.
- **v2 (`course_v2/`) is untouched.** Reference / record.
- **Card ids match filenames.** Composer enforces.
- **No external dependencies in the renderer.** HTML/CSS/JS only.
- **Markdown renderer in `composer.py` is minimal** — supports
  paragraphs, lists, blockquotes, code, bold/italic. Does NOT
  support tables, footnotes, or images. Add features only if
  authoring needs them.
