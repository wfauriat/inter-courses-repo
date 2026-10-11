#!/usr/bin/env python3
"""Compose a card library into a viewer-ready slide list.

Usage:
    python composer.py configs/<name>.yaml

Reads cards/*.md (YAML frontmatter + Markdown body), the named config,
and emits compositions/<format>.json — a flat list of slides.

The slide schema is deliberately simpler than v2's tree.json shape:
each card becomes one slide; no per-stage expansion; no figure
machinery. The renderer is a slide deck, not a refinement viewer.

Card schema (frontmatter):
    id: identifier matching filename
    role: spine | branch | example | hook
    thesis_role: load_bearing | enriching
    prerequisites: [card_id, ...]
    technical: bool (optional)
    time_cost: { short, standard, deep } seconds (optional)
    faces:
      general: |
        ...
      technical: |
        ...

Config schema (YAML):
    format: <output_filename_stem>
    audience: general | technical
    depth: short | standard | deep
    include_technical: bool
    budget_seconds: int (soft check)
    tree: nested list (the flattened DFS preorder is the slide order)

Tree shape: a YAML list. Each entry is either:
  - a bare card id (leaf): "alignment_thesis"
  - a single-key map { card_id: [children list] }: "embedding": [...]

Output: compositions/<format>.json with shape
    {
      "_meta": {...},
      "slides": [
        {"id", "title", "body_html", "role", "thesis_role",
         "parent", "beat", "technical", "notes"}, ...
      ]
    }
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).parent
CARDS_DIR = ROOT / "cards"
OUT_DIR = ROOT / "compositions"


# --- Minimal Markdown to HTML ----------------------------------------------

def _render_inline(text: str) -> str:
    """Inline markdown: bold, italic, inline code, and pass-through
    for ``$...$`` / ``$$...$$`` math (KaTeX renders client-side)."""
    parts: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        ch = text[i]
        # Inline code
        if ch == "`":
            j = text.find("`", i + 1)
            if j == -1:
                parts.append(html.escape(text[i:]))
                break
            parts.append("<code>" + html.escape(text[i + 1:j]) + "</code>")
            i = j + 1
            continue
        # Display math $$...$$
        if ch == "$" and i + 1 < n and text[i + 1] == "$":
            j = text.find("$$", i + 2)
            if j == -1:
                parts.append(html.escape(text[i:]))
                break
            parts.append("$$" + html.escape(text[i + 2:j]) + "$$")
            i = j + 2
            continue
        # Inline math $...$
        if ch == "$":
            j = text.find("$", i + 1)
            if j == -1:
                parts.append(html.escape(text[i:]))
                break
            parts.append("$" + html.escape(text[i + 1:j]) + "$")
            i = j + 1
            continue
        # Regular text up to next special char (` or $)
        next_indices = [k for k in (text.find("`", i), text.find("$", i))
                        if k != -1]
        if next_indices:
            j = min(next_indices)
            segment = text[i:j]
            i = j
        else:
            segment = text[i:]
            i = n
        seg = html.escape(segment)
        seg = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", seg)
        seg = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+?)(?<!\*)\*(?!\*)",
                     r"<em>\1</em>", seg)
        parts.append(seg)
    return "".join(parts)


def render_markdown(md: str) -> str:
    """Render a small subset of Markdown to HTML.

    Supports: paragraphs, headings (#/##/###), bullet lists (-, *),
    numbered lists (1.), blockquotes (>), code fences (```),
    horizontal rules (---), inline bold/italic/code.
    """
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Code fence
        if stripped.startswith("```"):
            i += 1
            buf = []
            while i < n and not lines[i].strip().startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            out.append("<pre><code>" + html.escape("\n".join(buf)) +
                       "</code></pre>")
            continue

        # Horizontal rule
        if re.match(r"^-{3,}$|^\*{3,}$", stripped):
            out.append("<hr/>")
            i += 1
            continue

        # Heading
        m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1))
            out.append(f"<h{level}>{_render_inline(m.group(2))}</h{level}>")
            i += 1
            continue

        # Blockquote
        if stripped.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            inner = render_markdown("\n".join(buf))
            out.append("<blockquote>" + inner + "</blockquote>")
            continue

        # Bulleted list
        if re.match(r"^[-*]\s+", stripped):
            buf = []
            while i < n and re.match(r"^[-*]\s+", lines[i].strip()):
                item = re.sub(r"^[-*]\s+", "", lines[i].strip())
                # Continuation lines (indented)
                i += 1
                while i < n and lines[i].startswith("  ") and lines[i].strip():
                    item += " " + lines[i].strip()
                    i += 1
                buf.append("<li>" + _render_inline(item) + "</li>")
            out.append("<ul>" + "".join(buf) + "</ul>")
            continue

        # Numbered list
        if re.match(r"^\d+\.\s+", stripped):
            buf = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                item = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                i += 1
                while i < n and lines[i].startswith("   ") and lines[i].strip():
                    item += " " + lines[i].strip()
                    i += 1
                buf.append("<li>" + _render_inline(item) + "</li>")
            out.append("<ol>" + "".join(buf) + "</ol>")
            continue

        # Blank line
        if not stripped:
            i += 1
            continue

        # Paragraph: collect contiguous non-blank, non-special lines
        buf = []
        while i < n and lines[i].strip() and \
                not re.match(r"^(#{1,6}\s|[-*]\s|\d+\.\s|>|```|---|\*\*\*)",
                             lines[i].strip()):
            buf.append(lines[i].rstrip())
            i += 1
        para = " ".join(line.strip() for line in buf)
        out.append("<p>" + _render_inline(para) + "</p>")

    return "\n".join(out)


# --- Card / Config Loading -------------------------------------------------

def parse_card(path: Path) -> dict[str, Any]:
    text = path.read_text()
    if not text.startswith("---\n"):
        raise ValueError(f"{path}: no leading frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise ValueError(f"{path}: no closing frontmatter")
    fm = yaml.safe_load(text[4:end])
    fm["_body"] = text[end + 5:]
    if "id" not in fm:
        raise ValueError(f"{path}: missing id")
    if path.stem != fm["id"]:
        raise ValueError(f"{path}: filename does not match id ({fm['id']})")
    return fm


def load_cards() -> dict[str, dict[str, Any]]:
    cards = {}
    for path in sorted(CARDS_DIR.glob("*.md")):
        card = parse_card(path)
        cards[card["id"]] = card
    return cards


def flatten_tree(tree_yaml: list, parent: str | None = None,
                 out: list | None = None) -> list[tuple[str, str | None]]:
    if out is None:
        out = []
    for entry in tree_yaml:
        if isinstance(entry, str):
            out.append((entry, parent))
        elif isinstance(entry, dict):
            for card_id, children in entry.items():
                out.append((card_id, parent))
                if children:
                    flatten_tree(children, parent=card_id, out=out)
        else:
            raise ValueError(f"unexpected tree entry: {entry!r}")
    return out


def card_to_title(card_id: str) -> str:
    return card_id.replace("_", " ").title()


# --- Composition -----------------------------------------------------------

def build_composition(config: dict, cards: dict[str, dict]) -> dict:
    audience = config.get("audience", "general")
    depth = config.get("depth", "standard")
    include_technical = config.get("include_technical", False)
    budget = config.get("budget_seconds", 1800)

    flat_all = flatten_tree(config["tree"])
    slides: list[dict] = []
    beat = 0
    last_role = None
    skip_subtree: set[str] = set()
    seen: set[str] = set()
    total_time = 0

    for card_id, parent in flat_all:
        if card_id not in cards:
            raise KeyError(f"unknown card id: {card_id}")
        card = cards[card_id]
        if parent in skip_subtree:
            skip_subtree.add(card_id)
            continue
        if not include_technical and card.get("technical"):
            skip_subtree.add(card_id)
            continue

        # Pick face + render any other authored faces too (for runtime toggle)
        faces = card.get("faces") or {}
        face_text = faces.get(audience)
        if face_text is None:
            face_text = faces.get("general")  # fallback
        if face_text is None:
            print(f"WARNING: {card_id} has no usable face for audience "
                  f"'{audience}' — skipping", file=sys.stderr)
            continue
        faces_html = {name: render_markdown(text)
                      for name, text in faces.items() if text}

        # Beat numbering: bumps when a spine/hook card appears at top level
        # (i.e., the parent is None).
        if parent is None and card.get("role") in ("spine", "hook"):
            beat += 1

        # Time bookkeeping
        tc = card.get("time_cost") or {}
        total_time += tc.get(depth, tc.get("standard", 60))

        slides.append({
            "id": card_id,
            "title": card_to_title(card_id),
            "body_html": render_markdown(face_text),
            "faces_html": faces_html,
            "default_face": audience if audience in faces_html else "general",
            "role": card.get("role"),
            "thesis_role": card.get("thesis_role"),
            "parent": parent,
            "beat": beat,
            "technical": bool(card.get("technical")),
            "notes": (card.get("notes_to_self") or "").strip(),
        })
        seen.add(card_id)

        # Soft prereq warning
        for prereq in card.get("prerequisites") or []:
            if prereq not in seen and prereq in cards \
                    and prereq not in skip_subtree:
                print(f"WARNING: {card_id} prereq {prereq} not yet in "
                      f"composition", file=sys.stderr)

    # Budget check
    print(f"Budget: {total_time/60:.1f}min total at {depth} depth "
          f"(target {budget/60:.1f}min)", file=sys.stderr)
    if total_time > budget * 1.2:
        print(f"WARNING: over budget", file=sys.stderr)
    elif total_time < budget * 0.5:
        print(f"NOTE: well under budget", file=sys.stderr)

    # Load-bearing presence check
    needed = {cid for cid, c in cards.items()
              if c.get("thesis_role") == "load_bearing"
              and (include_technical or not c.get("technical"))}
    missing = needed - seen
    if missing:
        print(f"NOTE: load-bearing cards not in composition: "
              f"{sorted(missing)}", file=sys.stderr)

    # Thesis-end check
    spine_seen = [s for s in slides if s["role"] in ("spine", "hook")]
    if spine_seen and spine_seen[-1]["id"] != "alignment_thesis":
        print(f"WARNING: composition does not end at alignment_thesis "
              f"(ends at {spine_seen[-1]['id']!r})", file=sys.stderr)

    return {
        "_meta": {
            "format": config.get("format"),
            "audience": audience,
            "depth": depth,
            "include_technical": include_technical,
            "total_time_seconds": total_time,
            "slide_count": len(slides),
        },
        "slides": slides,
    }


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(f"usage: {argv[0]} configs/<name>.yaml", file=sys.stderr)
        return 2
    config_path = Path(argv[1])
    if not config_path.exists():
        config_path = ROOT / argv[1]
    config = yaml.safe_load(config_path.read_text())
    cards = load_cards()
    comp = build_composition(config, cards)
    OUT_DIR.mkdir(exist_ok=True)
    fmt = config.get("format") or config_path.stem
    out_path = OUT_DIR / f"{fmt}.json"
    out_path.write_text(json.dumps(comp, indent=2))
    print(f"Wrote {out_path} ({comp['_meta']['slide_count']} slides)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
