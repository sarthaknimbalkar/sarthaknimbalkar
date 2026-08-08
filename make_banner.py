"""Generate the profile banner SVGs (dark + light).

GitHub renders README images as <img>, so no CSS, no JS, no webfonts survive.
SMIL animation does. Everything below is hand-authored SVG with a deterministic
pseudo-random field so the output is stable across regenerations.

The concept: a contribution grid where almost every cell is dark, because almost
every commit is private. A heat sweep passes over it and the hidden work glows
for a moment before going quiet again. That is the literal shape of the last year.

The grid is REAL day-by-day data out of stats.json (written by fetch_stats.py),
not decoration. Cell brightness tracks that day's actual contribution count, so
the shape of the year is the shape of the year.

Palette is lifted from sarthaknimbalkar.in so the two surfaces read as one brand.
"""

import json
import pathlib

W, H = 1280, 500

# Clean and minimal: a near-monochrome cool scheme, not the old muddy ember.
# The three grid "heat" colors are now just three cool tints of one hue, so the
# field reads as a single quiet material at varying depth instead of a rainbow.
# One restrained blue accent carries the period and the italic, nothing else.
DARK = dict(
    ink="#0a0b0e", fg="#eef1f5", dim="#7d8590", faint="#363c44", hair="#1a1e24",
    accent="#7aa2f7", ember="#2f3945", spark="#9cc0ff", glow="#7aa2f7",
    cell="#20262e", glow_op="0.05",
)
# The light-theme variant is NOT a pale mirror of the dark one. Saturated green
# only reads as neon against darkness; on a near-white ground it either vibrates
# or goes muddy. So this version is a deep forest slab that sits on GitHub's white
# page as a deliberate block of color, which is what lets the green actually glow.
LIGHT = dict(
    ink="#04150b", fg="#eafff0", dim="#7ba98a", faint="#3f6b4f", hair="#0f2e1b",
    accent="#3dff8f", ember="#00e05c", spark="#c9ff4d", glow="#3dff8f",
    cell="#123024", glow_op="0.20",
)

SERIF = "Georgia,'Iowan Old Style','Times New Roman',serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

# grid geometry, sized for GitHub's ~600px README card, not a full-bleed hero.
# Everything here is drawn at 1280 but SEEN at ~46%: type below ~18px SVG units
# is unreadable on the profile, so nothing on this canvas goes below 19.
COLS, ROWS = 53, 7
CELL, GAP = 16, 5
GRID_X, GRID_Y = (1280 - (53 * 21 - 5)) // 2, 232
SWEEP = 9.0  # seconds for one full pass, slow enough to feel like weather, not a ticker
PULSE = 3.4  # how long one cell takes to catch and die back down


def rnd(i):
    """Deterministic 0..1. Stable output, no import random, no drift between runs."""
    x = (i * 2654435761) ^ (i << 13)
    x = (x ^ (x >> 7)) * 2246822519 & 0xFFFFFFFF
    x = (x ^ (x >> 11)) * 3266489917 & 0xFFFFFFFF
    return ((x ^ (x >> 15)) & 0xFFFF) / 0xFFFF


def grid(c, weeks):
    """The field, rendered from real per-day counts. A quiet day stays a quiet day."""
    # Scale against the 65th percentile, not the max. A single 185-commit day would
    # otherwise flatten every ordinary day to near-black and kill the sweep.
    counts = sorted(n for w in weeks for n in w if n > 0)
    ceiling = max(counts[int(len(counts) * 0.65)], 1) if counts else 1

    out = []
    for col, week in enumerate(weeks[-COLS:]):
        for row, count in enumerate(week):
            if count <= 0:
                continue  # a genuinely empty day stays empty

            i = col * ROWS + row
            x = GRID_X + col * (CELL + GAP)
            y = GRID_Y + row * (CELL + GAP)
            # weight is how heavy that real day was, 0..1
            weight = min(count / ceiling, 1.0)
            # Cells rest in their OWN heat color at partial opacity, never in a
            # near-background grey: the grid must read as a burning field even
            # between sweep passes, especially at the ~46% scale GitHub shows.
            peak = c["spark"] if weight > 0.62 else c["accent"] if weight > 0.28 else c["ember"]
            peak_op = round(0.62 + 0.30 * weight, 3)
            rest_op = round(0.22 + 0.34 * weight, 3)
            delay = round(col / (COLS - 1) * SWEEP * 0.62 + rnd(i + 313) * 0.22, 3)

            # Fast attack, slow decay: the cell catches like something igniting
            # rather than easing politely in and out.
            kt = "0;0.18;1"
            beg = f"{delay}s;g.end+{delay}s"
            # scale pulse about the cell's own centre, so it swells as it fires
            cx, cy = x + CELL / 2, y + CELL / 2
            out.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="3" '
                f'fill="{peak}" opacity="{rest_op}">'
                f'<animate attributeName="fill" values="{peak};{c["spark"]};{peak}" '
                f'keyTimes="{kt}" dur="{PULSE}s" begin="{beg}" '
                f'calcMode="spline" keySplines="0.1 0.8 0.2 1;0.5 0 0.75 0.4"/>'
                f'<animate attributeName="opacity" values="{rest_op};{peak_op};{rest_op}" '
                f'keyTimes="{kt}" dur="{PULSE}s" begin="{beg}" '
                f'calcMode="spline" keySplines="0.1 0.8 0.2 1;0.5 0 0.75 0.4"/>'
                # Order matters. Additive transforms build a list applied left to
                # right, so translate must be emitted BEFORE scale to get
                # translate(t)·scale(s), which maps p to s*p + t. Then the
                # centre-preserving offset is exactly cx*(1-s). Emitting scale
                # first gives s*p + s*t and the cell visibly drifts as it swells.
                f'<animateTransform attributeName="transform" type="translate" '
                f'values="0 0;{round(-cx * 0.06, 2)} {round(-cy * 0.06, 2)};0 0" '
                f'keyTimes="{kt}" dur="{PULSE}s" begin="{beg}" additive="sum" '
                f'calcMode="spline" keySplines="0.1 0.8 0.2 1;0.5 0 0.75 0.4"/>'
                f'<animateTransform attributeName="transform" type="scale" '
                f'values="1;1.06;1" keyTimes="{kt}" dur="{PULSE}s" begin="{beg}" additive="sum" '
                f'calcMode="spline" keySplines="0.1 0.8 0.2 1;0.5 0 0.75 0.4"/>'
                f"</rect>"
            )
    return "\n".join(out)


def build(c, s):
    n_total = f"{s['total']:,}"
    pct = round(s["private"] / s["total"] * 100) if s["total"] else 0
    mid = W / 2
    grid_bottom = GRID_Y + ROWS * (CELL + GAP) - GAP
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="Sarthak Nimbalkar. Everything can be automated, except the one who automates. A year of contributions burning quietly in the dark, {pct} percent of them private.">
  <defs>
    <radialGradient id="halo" cx="50%" cy="18%" r="72%">
      <stop offset="0" stop-color="{c['glow']}" stop-opacity="{c['glow_op']}"/>
      <stop offset="1" stop-color="{c['glow']}" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="vig" cx="50%" cy="46%" r="76%">
      <stop offset="0.55" stop-color="{c['ink']}" stop-opacity="0"/>
      <stop offset="1" stop-color="#000000" stop-opacity="0.6"/>
    </radialGradient>
    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{c['accent']}" stop-opacity="0"/>
      <stop offset="0.5" stop-color="{c['accent']}" stop-opacity="0.7"/>
      <stop offset="1" stop-color="{c['accent']}" stop-opacity="0"/>
    </linearGradient>
    <filter id="grain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" stitchTiles="stitch"/>
      <feColorMatrix type="saturate" values="0"/>
      <feComponentTransfer><feFuncA type="linear" slope="0.055"/></feComponentTransfer>
    </filter>
  </defs>

  <rect width="{W}" height="{H}" fill="{c['ink']}"/>
  <rect width="{W}" height="{H}" fill="url(#halo)"/>

  <!-- master clock: every cell hangs its loop off this one element -->
  <rect id="clock" x="-10" y="-10" width="1" height="1" fill="none" opacity="0">
    <animate id="g" attributeName="opacity" from="0" to="0" dur="{SWEEP}s" repeatCount="indefinite"/>
  </rect>

  <!-- the hour this page is set in -->
  <text x="{mid}" y="52" text-anchor="middle" font-family="{MONO}" font-size="17" letter-spacing="5" fill="{c['faint']}">02:14 AM</text>

  <text x="{mid}" y="128" text-anchor="middle" font-family="{SERIF}" font-size="88" font-weight="500" letter-spacing="-2.5" fill="{c['fg']}">Sarthak Nimbalkar<tspan fill="{c['accent']}">.</tspan></text>

  <line x1="{mid - 180}" y1="156" x2="{mid + 180}" y2="156" stroke="url(#rule)" stroke-width="1"/>

  <text x="{mid}" y="192" text-anchor="middle" font-family="{MONO}" font-size="20" letter-spacing="0.4" fill="{c['dim']}">Everything can be automated. <tspan fill="{c['accent']}" font-style="italic">Except the one who automates.</tspan></text>

{grid(c, s['weeks'])}

  <text x="{mid}" y="{grid_bottom + 52}" text-anchor="middle" font-family="{MONO}" font-size="19" letter-spacing="0.8" fill="{c['faint']}">{n_total} contributions this year<tspan fill="{c['dim']}"> · </tspan><tspan fill="{c['accent']}">{pct}% of them where you cannot see</tspan><tspan fill="{c['dim']}"> · </tspan>shipping since {s['since']}</text>

  <rect width="{W}" height="{H}" fill="url(#vig)"/>
  <rect width="{W}" height="{H}" filter="url(#grain)" opacity="1" fill="none" pointer-events="none"/>
</svg>
'''


if __name__ == "__main__":
    here = pathlib.Path(__file__).parent
    s = json.loads((here / "stats.json").read_text(encoding="utf-8"))
    out = here / "assets"
    out.mkdir(exist_ok=True)
    (out / "banner-dark.svg").write_text(build(DARK, s), encoding="utf-8")
    (out / "banner-light.svg").write_text(build(LIGHT, s), encoding="utf-8")
    print(f"wrote banners from stats.json (total={s['total']:,} private={s['private']:,})")
