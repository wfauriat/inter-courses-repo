"""
build_interactive_token_vector_svg.py
=====================================

Generate interactive_talk/resources/token_vector.svg — a schematic 3D
triad with two mock-coordinate vectors. Pedagogical anchor for "a token
becomes a vector in space: here is what such a vector looks like, with
concrete numerical coordinates on each axis."

No embedding backend: hand-picked mock values. Real embeddings live in
~100 to ~10_000 dimensions; the 3D drawing is a visual handle.

Two layers keyed to tree.json `show` lists:
    id1   vector1 + corner-path + axis feet + right-side column vector
    id2   vector2 + ... (same pattern)
Base (always visible): axes, axis labels, origin, title.

Color-coding: every element tied to a coordinate axis inherits that
axis's color — axis line, axis label, drop-segment along that axis,
foot dot, foot numerical value, and the matching row in the column
vector. The two vectors themselves carry per-identity colors so id1
vs id2 read as "different token".
"""

from __future__ import annotations

import os


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT  = os.path.dirname(SCRIPT_DIR)
OUT_SVG    = os.path.join(REPO_ROOT, "interactive_talk", "resources",
                          "token_vector.svg")

WIDTH, HEIGHT = 720, 500
ORIGIN_X, ORIGIN_Y = 250, 310      # pixel position of 3D origin
SCALE         = 55                  # pixels per world unit (x and z)
DEPTH_COS     = 0.866                # cos(30°): y-axis depth direction
DEPTH_SIN     = 0.5                  # sin(30°)
DEPTH_SCALE   = 0.65                 # y-axis foreshortening for 3D feel

# Axis colors — same color family identifies an axis everywhere it appears
X_COLOR = "#DD8452"   # warm coral
Y_COLOR = "#55A868"   # green
Z_COLOR = "#4C9BD1"   # sky blue

# Vector identities
VEC1_COLOR = "#C77CB5"   # pink / mauve
VEC2_COLOR = "#D4A017"   # amber / gold

LABEL_COLOR = "#e8e8e8"
TITLE_COLOR = "#b8b8b8"
DIM_COLOR   = "#888"

# Mock coordinate values — chosen for visual spread, includes a negative
# component on V2 so layman viewers see coords can be any real number.
V1 = (1.5, 2.0, 1.0)
V2 = (2.0, -1.0, 1.5)


def project(x: float, y: float, z: float) -> tuple[float, float]:
    """Right-handed (x, y, z) world → 2D screen pixels. x-axis goes
    lower-left (foreshortened, showing depth toward the viewer);
    y-axis goes horizontal right; z-axis goes vertical up. SVG y grows
    downward, hence the sign flips."""
    px = ORIGIN_X + y * SCALE - x * SCALE * DEPTH_COS * DEPTH_SCALE
    py = ORIGIN_Y + x * SCALE * DEPTH_SIN * DEPTH_SCALE - z * SCALE
    return px, py


def fmt_foot(v: float) -> str:
    """Axis foot labels: bare number, minus sign only when negative.
    '+' prefix for positives is dropped so adjacent labels (id1+id2
    x-feet, for instance) don't jam into each other."""
    return f"{v:.1f}"


def fmt_col(v: float) -> str:
    """Column-vector entry: always-signed, for clean vertical alignment
    of a mixed positive / negative vector."""
    return f"{v:+.1f}"


def marker_def(id_: str, color: str) -> str:
    return (
        f'    <marker id="{id_}" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">\n'
        f'      <path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/>\n'
        '    </marker>'
    )


def vec_layer(layer_id: str,
              v: tuple[float, float, float],
              color: str,
              column_y: int) -> list[str]:
    """Emit the per-vector layer group: parallelogram-in-xOy-plane +
    vertical rise to V, axis-foot markers, main arrow, right-side
    coordinate column."""
    vx, vy, vz = v
    p_o      = project(0, 0, 0)
    p_v      = project(vx, vy, vz)
    p_x_foot = project(vx, 0, 0)     # X-corner of parallelogram
    p_y_foot = project(0, vy, 0)     # Y-corner of parallelogram
    p_z_foot = project(0, 0, vz)     # Foot on z-axis
    p_xy     = project(vx, vy, 0)    # Floor corner — xOy-plane projection of V

    fx_foot, fy_foot, fz_foot = fmt_foot(vx), fmt_foot(vy), fmt_foot(vz)
    fx_col, fy_col, fz_col = fmt_col(vx), fmt_col(vy), fmt_col(vz)

    out = [f'  <g class="layer" id="{layer_id}">']

    # Parallelogram in xOy plane + vertical rise. Two axis-aligned edges
    # close the parallelogram O-X-XY-Y (the other two sides lie on the
    # axes themselves); a third segment climbs from XY-corner to V.
    #   X-corner → XY-corner : length |vy|, parallel to y-axis → Y_COLOR
    #   Y-corner → XY-corner : length |vx|, parallel to x-axis → X_COLOR
    #   XY-corner → V        : length |vz|, parallel to z-axis → Z_COLOR
    out.append('    <g stroke-dasharray="4,3" stroke-width="1.3" '
               'opacity="0.85" fill="none">')
    out.append(f'      <line x1="{p_x_foot[0]:.1f}" y1="{p_x_foot[1]:.1f}" '
               f'x2="{p_xy[0]:.1f}" y2="{p_xy[1]:.1f}" '
               f'stroke="{Y_COLOR}"/>')
    out.append(f'      <line x1="{p_y_foot[0]:.1f}" y1="{p_y_foot[1]:.1f}" '
               f'x2="{p_xy[0]:.1f}" y2="{p_xy[1]:.1f}" '
               f'stroke="{X_COLOR}"/>')
    out.append(f'      <line x1="{p_xy[0]:.1f}" y1="{p_xy[1]:.1f}" '
               f'x2="{p_v[0]:.1f}" y2="{p_v[1]:.1f}" '
               f'stroke="{Z_COLOR}"/>')
    out.append('    </g>')

    # Axis-foot markers with numerical coordinate values. Label anchor
    # chosen per rotated-axis layout: x-axis points lower-left (label
    # further lower-left of the foot), y-axis points horizontal-right
    # (label below the foot), z-axis points up (label left of the foot).
    out.append('    <g font-size="11" font-weight="600">')
    out.append(f'      <circle cx="{p_x_foot[0]:.1f}" cy="{p_x_foot[1]:.1f}" '
               f'r="3.2" fill="{X_COLOR}"/>')
    out.append(f'      <text x="{p_x_foot[0] - 9:.1f}" y="{p_x_foot[1] + 12:.1f}" '
               f'text-anchor="end" fill="{X_COLOR}">{fx_foot}</text>')
    out.append(f'      <circle cx="{p_y_foot[0]:.1f}" cy="{p_y_foot[1]:.1f}" '
               f'r="3.2" fill="{Y_COLOR}"/>')
    out.append(f'      <text x="{p_y_foot[0]:.1f}" y="{p_y_foot[1] + 16:.1f}" '
               f'text-anchor="middle" fill="{Y_COLOR}">{fy_foot}</text>')
    out.append(f'      <circle cx="{p_z_foot[0]:.1f}" cy="{p_z_foot[1]:.1f}" '
               f'r="3.2" fill="{Z_COLOR}"/>')
    out.append(f'      <text x="{p_z_foot[0] - 9:.1f}" y="{p_z_foot[1] + 4:.1f}" '
               f'text-anchor="end" fill="{Z_COLOR}">{fz_foot}</text>')
    out.append('    </g>')

    # Main vector arrow from origin.
    out.append(f'    <line x1="{p_o[0]:.1f}" y1="{p_o[1]:.1f}" '
               f'x2="{p_v[0]:.1f}" y2="{p_v[1]:.1f}" stroke="{color}" '
               f'stroke-width="2.6" marker-end="url(#arrow-{layer_id})"/>')
    out.append(f'    <text x="{p_v[0] + 10:.1f}" y="{p_v[1] - 9:.1f}" '
               f'font-size="14" font-weight="700" fill="{color}">{layer_id}</text>')

    # Right-side column vector. Brackets are simple L-shaped paths.
    bx_l, bx_r = 560, 680
    top = column_y - 16
    bot = column_y + 54
    mid = (bx_l + bx_r) / 2
    out.append('    <g font-family="monospace" font-size="14" font-weight="600">')
    out.append(f'      <text x="{bx_l - 8:.1f}" y="{column_y + 22:.1f}" '
               f'text-anchor="end" fill="{color}">{layer_id} =</text>')
    out.append(f'      <path d="M {bx_l + 8} {top} L {bx_l} {top} '
               f'L {bx_l} {bot} L {bx_l + 8} {bot}" '
               f'stroke="{DIM_COLOR}" stroke-width="1.5" fill="none"/>')
    out.append(f'      <path d="M {bx_r - 8} {top} L {bx_r} {top} '
               f'L {bx_r} {bot} L {bx_r - 8} {bot}" '
               f'stroke="{DIM_COLOR}" stroke-width="1.5" fill="none"/>')
    out.append(f'      <text x="{mid:.1f}" y="{column_y + 6:.1f}" '
               f'text-anchor="middle" fill="{X_COLOR}">{fx_col}</text>')
    out.append(f'      <text x="{mid:.1f}" y="{column_y + 26:.1f}" '
               f'text-anchor="middle" fill="{Y_COLOR}">{fy_col}</text>')
    out.append(f'      <text x="{mid:.1f}" y="{column_y + 46:.1f}" '
               f'text-anchor="middle" fill="{Z_COLOR}">{fz_col}</text>')
    out.append('    </g>')

    out.append('  </g>')
    return out


def build_svg() -> str:
    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'font-family="Iosevka, \'JetBrains Mono\', monospace">')
    lines.append('  <!--')
    lines.append('    Generated by workspace/build_interactive_token_vector_svg.py')
    lines.append('    Pure mock geometry — no embedding backend. Edit and rerun.')
    lines.append('  -->')

    # Arrow markers
    lines.append('  <defs>')
    lines.append(marker_def("axis-x", X_COLOR))
    lines.append(marker_def("axis-y", Y_COLOR))
    lines.append(marker_def("axis-z", Z_COLOR))
    lines.append(marker_def("arrow-id1", VEC1_COLOR))
    lines.append(marker_def("arrow-id2", VEC2_COLOR))
    lines.append('  </defs>')

    # Title
    lines.append(
        f'  <text x="{WIDTH // 2}" y="28" text-anchor="middle" '
        f'fill="{TITLE_COLOR}" font-size="15" font-weight="500">'
        'Each token is a vector — a list of numerical coordinates'
        '</text>')

    # Axes — colored lines, arrowheads at positive tips.
    x_neg = project(-1, 0, 0); x_pos = project(3.2, 0, 0)
    y_neg = project(0, -1.4, 0); y_pos = project(0, 3.2, 0)
    z_neg = project(0, 0, -1); z_pos = project(0, 0, 3.2)
    lines.append('  <g stroke-width="1.8" fill="none" opacity="0.9">')
    lines.append(f'    <line x1="{x_neg[0]:.1f}" y1="{x_neg[1]:.1f}" '
                 f'x2="{x_pos[0]:.1f}" y2="{x_pos[1]:.1f}" '
                 f'stroke="{X_COLOR}" marker-end="url(#axis-x)"/>')
    lines.append(f'    <line x1="{y_neg[0]:.1f}" y1="{y_neg[1]:.1f}" '
                 f'x2="{y_pos[0]:.1f}" y2="{y_pos[1]:.1f}" '
                 f'stroke="{Y_COLOR}" marker-end="url(#axis-y)"/>')
    lines.append(f'    <line x1="{z_neg[0]:.1f}" y1="{z_neg[1]:.1f}" '
                 f'x2="{z_pos[0]:.1f}" y2="{z_pos[1]:.1f}" '
                 f'stroke="{Z_COLOR}" marker-end="url(#axis-z)"/>')
    lines.append('  </g>')

    # Axis labels at positive tips. x-tip sits lower-left, y-tip right,
    # z-tip up; labels offset further along each axis direction.
    lines.append('  <g font-size="15" font-weight="700" '
                 'font-family="monospace">')
    lines.append(f'    <text x="{x_pos[0] - 8:.1f}" y="{x_pos[1] + 14:.1f}" '
                 f'text-anchor="end" fill="{X_COLOR}">x</text>')
    lines.append(f'    <text x="{y_pos[0] + 10:.1f}" y="{y_pos[1] + 5:.1f}" '
                 f'fill="{Y_COLOR}">y</text>')
    lines.append(f'    <text x="{z_pos[0] + 9:.1f}" y="{z_pos[1] - 4:.1f}" '
                 f'fill="{Z_COLOR}">z</text>')
    lines.append('  </g>')

    # Origin dot + "0" label. Upper-left of origin — away from all three
    # axes (x goes lower-left, y goes right, z goes up).
    lines.append(f'  <circle cx="{ORIGIN_X}" cy="{ORIGIN_Y}" r="3" '
                 f'fill="{LABEL_COLOR}"/>')
    lines.append(f'  <text x="{ORIGIN_X - 8:.1f}" y="{ORIGIN_Y - 6:.1f}" '
                 f'text-anchor="end" fill="{DIM_COLOR}" font-size="11">0</text>')

    # Per-vector layers.
    lines.extend(vec_layer("id1", V1, VEC1_COLOR, column_y=130))
    lines.extend(vec_layer("id2", V2, VEC2_COLOR, column_y=290))

    lines.append('</svg>')
    return "\n".join(lines) + "\n"


def main() -> None:
    os.makedirs(os.path.dirname(OUT_SVG), exist_ok=True)
    svg = build_svg()
    with open(OUT_SVG, "w") as f:
        f.write(svg)
    print(f"Wrote {OUT_SVG}")


if __name__ == "__main__":
    main()
