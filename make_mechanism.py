"""The retry storm, drawn by hand in the same palette as everything else on the page.

Mermaid would draw this too, but in its own default colours, inside a cross-origin
iframe, and not at all inside a collapsed <details>. Drawing it directly costs one
file and keeps the page one object instead of two visual languages.

The point of the picture is the edge that goes backwards: the failure feeds the
retries and the retries feed the failure, so the loop has no exit of its own.
"""

import pathlib

W = 900
BOX_W, BOX_H = 190, 74
ROW_Y = 214
GAP = 14
X0 = 40
EXIT_DROP = 54          # gap between the stage row and the outage box

# Derive the canvas from the content. Hardcoding this is how the outage box got
# clipped when the formula moved out to the markdown.
H = ROW_Y + BOX_H + EXIT_DROP + BOX_H + 34

SERIF = "Georgia,'Iowan Old Style','Times New Roman',serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"

DARK = dict(ink="#0b0907", fg="#e8ddc9", dim="#8d8171", faint="#5b5344", hair="#2b2219",
            accent="#ffa028", ember="#ff5330", spark="#ffd76a", panel="#15110d")
LIGHT = dict(ink="#04150b", fg="#eafff0", dim="#7ba98a", faint="#3d6b4e", hair="#0f2e1b",
             accent="#3dff8f", ember="#00e05c", spark="#c9ff4d", panel="#0a2416")


def box(x, y, w, h, l1, l2, c, stroke, dashed=False, label_col=None):
    dash = ' stroke-dasharray="5 4"' if dashed else ""
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="7" fill="{c["panel"]}" '
           f'stroke="{stroke}" stroke-width="1.6"{dash}/>']
    cx = x + w / 2
    out.append(f'<text x="{cx}" y="{y + 30}" text-anchor="middle" font-family="{MONO}" '
               f'font-size="14.5" font-weight="700" fill="{label_col or c["fg"]}">{l1}</text>')
    out.append(f'<text x="{cx}" y="{y + 52}" text-anchor="middle" font-family="{MONO}" '
               f'font-size="14.5" fill="{c["dim"]}">{l2}</text>')
    return "".join(out)


def build(c):
    xs = [X0 + i * (BOX_W + GAP) for i in range(4)]
    cy = ROW_Y + BOX_H / 2
    p = []

    p.append(f'<rect width="{W}" height="{H}" fill="{c["ink"]}"/>')
    p.append(f'<text x="{X0}" y="52" font-family="{SERIF}" font-size="30" fill="{c["fg"]}">'
             f'A 412 millisecond fault, amplified into two hours<tspan fill="{c["accent"]}">.</tspan></text>')
    p.append(f'<text x="{X0}" y="82" font-family="{MONO}" font-size="15" letter-spacing="0.4" '
             f'fill="{c["faint"]}">THE DEPENDENCY RECOVERED IMMEDIATELY. THE CLIENTS DID NOT.</text>')

    # the four stages
    p.append(box(xs[0], ROW_Y, BOX_W, BOX_H, "dependency gone", "412 ms", c, c["ember"],
                 label_col=c["ember"]))
    p.append(box(xs[1], ROW_Y, BOX_W, BOX_H, "8,800 clients fail", "at the same instant", c, c["hair"]))
    p.append(box(xs[2], ROW_Y, BOX_W, BOX_H, "all of them retry", "at exactly +1.000 s", c, c["hair"]))
    p.append(box(xs[3], ROW_Y, BOX_W, BOX_H, "8,800 arrive inside", "one millisecond",
                 c, c["accent"], label_col=c["accent"]))

    # forward arrows
    for i in range(3):
        x1 = xs[i] + BOX_W
        x2 = xs[i + 1]
        p.append(f'<line x1="{x1 + 3}" y1="{cy}" x2="{x2 - 9}" y2="{cy}" stroke="{c["dim"]}" '
                 f'stroke-width="1.6" marker-end="url(#a)"/>')

    # the edge that goes backwards: this is the whole story
    top = ROW_Y - 16
    arc_y = ROW_Y - 66
    sx, ex = xs[3] + BOX_W / 2, xs[1] + BOX_W / 2
    p.append(f'<path d="M {sx} {top} C {sx} {arc_y}, {ex} {arc_y}, {ex} {top - 2}" fill="none" '
             f'stroke="{c["spark"]}" stroke-width="2.2" marker-end="url(#s)"/>')
    p.append(f'<text x="{(sx + ex) / 2}" y="{arc_y - 8}" text-anchor="middle" font-family="{MONO}" '
             f'font-size="14.5" font-weight="700" fill="{c["spark"]}">they fail together, so they '
             f'retry together, so they fail together</text>')

    # the exit
    oy = ROW_Y + BOX_H + EXIT_DROP
    p.append(f'<line x1="{xs[3] + BOX_W / 2}" y1="{ROW_Y + BOX_H + 3}" x2="{xs[3] + BOX_W / 2}" '
             f'y2="{oy - 9}" stroke="{c["ember"]}" stroke-width="1.6" marker-end="url(#e)"/>')
    p.append(box(xs[3], oy, BOX_W, BOX_H, "gateway saturates", "2 h 11 m outage", c, c["ember"],
                 dashed=True, label_col=c["ember"]))

    defs = "".join(
        f'<marker id="{i}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto"><path d="M 0 0 L 10 5 L 0 10 z" fill="{col}"/></marker>'
        for i, col in (("a", c["dim"]), ("s", c["spark"]), ("e", c["ember"])))

    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            f'role="img" aria-label="A 412 millisecond dependency fault fails 8,800 clients at the '
            f'same instant. All of them retry at exactly one second, landing on the same millisecond, '
            f'which fails them again. The loop feeds itself and saturates the gateway for two hours '
            f'eleven minutes.">'
            f'<defs>{defs}</defs>' + "".join(p) + "</svg>")


if __name__ == "__main__":
    out = pathlib.Path(__file__).parent / "assets"
    out.mkdir(exist_ok=True)
    for name, pal in (("dark", DARK), ("light", LIGHT)):
        f = out / f"mechanism-{name}.svg"
        f.write_text(build(pal), encoding="utf-8")
        print(f"{f.name}: {f.stat().st_size // 1024} KB")
