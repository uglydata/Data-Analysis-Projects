"""
Minimal multi-line SVG chart, standard library only (renders directly on GitHub).

line_chart(lines, ...) where each line is {"name", "points": [(x, y), ...], "highlight": bool, "bold": bool}.
Highlighted lines get a colour and an end label; the rest are thin grey context lines.
"""

from html import escape

PALETTE = ["#1f2937", "#9e3039", "#2563eb", "#0f766e", "#b45309", "#7c3aed", "#be185d", "#4d7c0f"]
GREY = "#c7cbd3"
W, H = 820, 480
M = {"l": 52, "r": 190, "t": 70, "b": 64}


def _nice_ticks(lo, hi, n=6):
    step = (hi - lo) / n
    mag = 10 ** len(str(int(step))) / 10 if step >= 1 else 1
    step = next(s * mag for s in (1, 2, 2.5, 5, 10) if s * mag >= step)
    start = (lo // step) * step
    ticks, t = [], start
    while t <= hi + 1e-9:
        ticks.append(round(t, 6))
        t += step
    return ticks


def line_chart(lines, title, subtitle="", source="", baseline=None):
    xs = sorted({x for ln in lines for x, _ in ln["points"]})
    ys = [y for ln in lines for _, y in ln["points"]] + ([baseline] if baseline is not None else [])
    ticks = _nice_ticks(min(ys), max(ys))
    y0, y1 = ticks[0], ticks[-1]
    pw, ph = W - M["l"] - M["r"], H - M["t"] - M["b"]

    def sx(x):
        return M["l"] + (x - xs[0]) / (xs[-1] - xs[0]) * pw

    def sy(y):
        return M["t"] + (1 - (y - y0) / (y1 - y0)) * ph

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'font-family="Segoe UI, Helvetica, Arial, sans-serif">',
           f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
           f'<text x="{M["l"]}" y="28" font-size="17" font-weight="600" fill="#111827">{escape(title)}</text>',
           f'<text x="{M["l"]}" y="48" font-size="12" fill="#6b7280">{escape(subtitle)}</text>']
    for t in ticks:
        out.append(f'<line x1="{M["l"]}" x2="{M["l"] + pw}" y1="{sy(t):.1f}" y2="{sy(t):.1f}" stroke="#eceef2"/>')
        out.append(f'<text x="{M["l"] - 8}" y="{sy(t) + 4:.1f}" font-size="11" fill="#6b7280" text-anchor="end">{t:g}</text>')
    if baseline is not None:
        out.append(f'<line x1="{M["l"]}" x2="{M["l"] + pw}" y1="{sy(baseline):.1f}" y2="{sy(baseline):.1f}" '
                   f'stroke="#9ca3af" stroke-dasharray="4 3"/>')
    for x in xs:
        out.append(f'<text x="{sx(x):.1f}" y="{M["t"] + ph + 18}" font-size="11" fill="#6b7280" text-anchor="middle">{x}</text>')

    def path(pts):
        return "M" + " L".join(f"{sx(x):.1f},{sy(y):.1f}" for x, y in pts)

    for ln in (l for l in lines if not l["highlight"]):
        out.append(f'<path d="{path(ln["points"])}" fill="none" stroke="{GREY}" stroke-width="1.2"/>')
    hl = [l for l in lines if l["highlight"]]
    labels = []
    for i, ln in enumerate(hl):
        color = PALETTE[i % len(PALETTE)]
        width = 3 if ln.get("bold") else 2
        out.append(f'<path d="{path(ln["points"])}" fill="none" stroke="{color}" stroke-width="{width}" '
                   f'stroke-linecap="round" stroke-linejoin="round"/>')
        x, y = ln["points"][-1]
        out.append(f'<circle cx="{sx(x):.1f}" cy="{sy(y):.1f}" r="3.5" fill="{color}"/>')
        labels.append([sy(y), f'{ln["name"]} {y:g}', color])
    labels.sort()
    for i in range(1, len(labels)):           # push end labels apart so they never overlap
        labels[i][0] = max(labels[i][0], labels[i - 1][0] + 15)
    for ty, text, color in labels:
        out.append(f'<text x="{M["l"] + pw + 10}" y="{ty + 4:.1f}" font-size="12" fill="{color}" font-weight="600">{escape(text)}</text>')
    out.append(f'<text x="{M["l"]}" y="{H - 14}" font-size="11" fill="#6b7280">{escape(source)}</text>')
    out.append("</svg>")
    return "\n".join(out)
