"""Minimal dependency-free SVG chart primitives.
Palette validated via dataviz validate_palette.js (light mode, 3 categorical slots, all checks PASS;
aqua #1baf7a sits below 3:1 on light so the relief rule applies -> every aqua mark carries a direct label)."""

S1, S2, S3 = "var(--series-1)", "var(--series-2)", "var(--series-3)"
INK, INK2, INK3 = "var(--text-primary)", "var(--text-secondary)", "var(--text-muted)"
GRID, SURF = "var(--grid)", "var(--surface-1)"

def esc(s):
    return (str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;"))

def _open(w, h, cls="chart"):
    return (f'<svg class="{cls}" viewBox="0 0 {w} {h}" role="img" '
            f'preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">')

def hbar(rows, w=760, rowh=30, pad_l=250, pad_r=90, pad_t=14, pad_b=30, fmt="{:.1f}", note=None):
    """rows: [(label, value, color, optional_sublabel)]"""
    h = pad_t + rowh*len(rows) + pad_b
    mx = max(r[1] for r in rows) or 1
    span = w - pad_l - pad_r
    o = [_open(w, h)]
    for i, r in enumerate(rows):
        lab, val, col = r[0], r[1], r[2]
        sub = r[3] if len(r) > 3 else None
        y = pad_t + i*rowh
        bw = max(2, span * (val/mx))
        o.append(f'<text x="{pad_l-12}" y="{y+rowh/2+4}" text-anchor="end" class="lbl">{esc(lab)}</text>')
        o.append(f'<rect x="{pad_l}" y="{y+5}" width="{bw:.1f}" height="{rowh-12}" rx="4" fill="{col}"/>')
        o.append(f'<text x="{pad_l+bw+8}" y="{y+rowh/2+4}" class="val">{fmt.format(val)}'
                 f'{"  " + esc(sub) if sub else ""}</text>')
    if note:
        o.append(f'<text x="{pad_l}" y="{h-8}" class="note">{esc(note)}</text>')
    o.append("</svg>")
    return "".join(o)

def grouped(cats, series, w=760, h=300, pad_l=60, pad_r=16, pad_t=18, pad_b=56, fmt="{:.0f}", ymax=None, ylab=None):
    """cats: [str]; series: [(name, [vals], color)]"""
    mx = ymax or max(max(s[1]) for s in series)
    mx = mx * 1.14 or 1
    pw = (w - pad_l - pad_r) / len(cats)
    n = len(series)
    bw = min(34, (pw - 16) / n)
    o = [_open(w, h)]
    for t in range(5):
        v = mx*t/4; y = h - pad_b - (h-pad_t-pad_b)*(t/4)
        o.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        o.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" class="ax">{fmt.format(v)}</text>')
    for ci, c in enumerate(cats):
        gx = pad_l + pw*ci + pw/2
        for si, (nm, vals, col) in enumerate(series):
            v = vals[ci]
            if v is None: continue
            bh = (h-pad_t-pad_b) * (v/mx)
            x = gx - (n*bw+ (n-1)*2)/2 + si*(bw+2)
            o.append(f'<rect x="{x:.1f}" y="{h-pad_b-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" fill="{col}"/>')
            o.append(f'<text x="{x+bw/2:.1f}" y="{h-pad_b-bh-6:.1f}" text-anchor="middle" class="val">{fmt.format(v)}</text>')
        o.append(f'<text x="{gx:.1f}" y="{h-pad_b+18}" text-anchor="middle" class="ax">{esc(c)}</text>')
    if ylab:
        o.append(f'<text x="{pad_l-8}" y="{pad_t-6}" text-anchor="end" class="note">{esc(ylab)}</text>')
    o.append("</svg>")
    return "".join(o)

def legend(items):
    sw = "".join(f'<span class="key"><i style="background:{c}"></i>{esc(n)}</span>' for n, c in items)
    return f'<div class="legend">{sw}</div>'

def scatter(pts, w=760, h=420, pad_l=64, pad_r=24, pad_t=20, pad_b=54, xlab="", ylab=""):
    """pts: [(x, y, label, color, radius, emphasize)] — log10 y axis."""
    import math
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    xmin, xmax = 0, max(xs)*1.15
    ymin, ymax = 0.6, max(ys)*2.2
    def X(v): return pad_l + (w-pad_l-pad_r)*(v-xmin)/(xmax-xmin)
    def Y(v): 
        lo, hi = math.log10(ymin), math.log10(ymax)
        return h-pad_b - (h-pad_t-pad_b)*((math.log10(max(v,ymin))-lo)/(hi-lo))
    o = [_open(w, h)]
    for dec in [1, 10, 100, 1000]:
        if dec > ymax: break
        y = Y(dec)
        o.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        o.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" class="ax">{dec}</text>')
    for t in range(0, int(xmax)+1, 2):
        x = X(t)
        o.append(f'<line x1="{x:.1f}" y1="{pad_t}" x2="{x:.1f}" y2="{h-pad_b}" stroke="{GRID}" stroke-width="1" opacity=".5"/>')
        o.append(f'<text x="{x:.1f}" y="{h-pad_b+18}" text-anchor="middle" class="ax">{t}</text>')
    order = sorted(pts, key=lambda p: -p[4])
    for (x, y, lab, col, r, emph) in order:          # all marks first
        o.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{r}" fill="{col}" '
                 f'stroke="{SURF}" stroke-width="2" opacity="{0.95 if emph else 0.8}"/>')
    placed = []
    marks = [(X(px), Y(py), pr) for (px, py, _, _, pr, _) in pts]
    for (x, y, lab, col, r, emph) in order:          # then labels, on top
        cx, cy = X(x), Y(y)
        anchor = "end" if cx > w*0.68 else "start"
        dx = -(r+6) if anchor == "end" else (r+6)
        est = 6.4*len(lab) + 6
        lx = cx+dx
        x0, x1 = (lx-est, lx) if anchor == "end" else (lx, lx+est)
        ly = cy+4
        def clash(yy):
            if any(abs(yy-py) < 12.5 and not (x1 < px0-4 or x0 > px1+4)
                   for px0, py, px1 in placed):
                return True
            return any(abs(yy-4-my) < mr+5 and x0-mr-2 < mx < x1+mr+2
                       for mx, my, mr in marks if abs(mx-cx) > 1 or abs(my-cy) > 1)
        for _ in range(40):
            if not clash(ly): break
            ly += 12.5
        if ly - cy > 8:
            o.append(f'<line x1="{cx:.1f}" y1="{cy:.1f}" x2="{lx:.1f}" y2="{ly-3.5:.1f}" '
                     f'stroke="{GRID}" stroke-width="1"/>')
        placed.append((x0, ly, x1))
        o.append(f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" '
                 f'style="paint-order:stroke;stroke:{SURF};stroke-width:3.5px;stroke-linejoin:round" '
                 f'class="{"val emph" if emph else "val"}">{esc(lab)}</text>')
    o.append(f'<text x="{w/2}" y="{h-8}" text-anchor="middle" class="note">{esc(xlab)}</text>')
    o.append(f'<text x="12" y="{pad_t+2}" class="note">{esc(ylab)}</text>')
    o.append("</svg>")
    return "".join(o)

def heatmap(rows, cols, cells, w=760, cellh=26, pad_l=230, pad_r=90, pad_t=30, note=None):
    """cells[r][c] = 0..3 intensity or None."""
    ramp = ["#eef2f6", "#b7d3f6", "#5598e7", "#1c5cab"]
    cw = (w - pad_l - pad_r) / len(cols)
    h = pad_t + cellh*len(rows) + 30
    o = [_open(w, h)]
    for ci, c in enumerate(cols):
        o.append(f'<text x="{pad_l+cw*ci+cw/2:.1f}" y="{pad_t-10}" text-anchor="middle" class="ax">{esc(c)}</text>')
    for ri, r in enumerate(rows):
        y = pad_t + cellh*ri
        o.append(f'<text x="{pad_l-12}" y="{y+cellh/2+4}" text-anchor="end" class="lbl">{esc(r)}</text>')
        for ci in range(len(cols)):
            v = cells[ri][ci]
            fill = ramp[v] if v is not None else "transparent"
            o.append(f'<rect x="{pad_l+cw*ci+1:.1f}" y="{y+1}" width="{cw-2:.1f}" height="{cellh-2}" rx="3" fill="{fill}"/>')
    if note:
        o.append(f'<text x="{pad_l}" y="{h-8}" class="note">{esc(note)}</text>')
    o.append("</svg>")
    return "".join(o)

def lines(xlabels, series, w=760, h=300, pad_l=52, pad_r=90, pad_t=20, pad_b=48):
    """series: [(name, [vals], color)]"""
    mx = max(max(v for v in s[1] if v is not None) for s in series) * 1.15 or 1
    sx = (w-pad_l-pad_r)/(len(xlabels)-1)
    o = [_open(w, h)]
    for t in range(5):
        v = mx*t/4; y = h-pad_b-(h-pad_t-pad_b)*(t/4)
        o.append(f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w-pad_r}" y2="{y:.1f}" stroke="{GRID}" stroke-width="1"/>')
        o.append(f'<text x="{pad_l-8}" y="{y+4:.1f}" text-anchor="end" class="ax">{v:.0f}</text>')
    for i, lab in enumerate(xlabels):
        o.append(f'<text x="{pad_l+sx*i:.1f}" y="{h-pad_b+18}" text-anchor="middle" class="ax">{esc(lab)}</text>')
    ends = []
    for nm, vals, col in series:
        pts = [(pad_l+sx*i, h-pad_b-(h-pad_t-pad_b)*(v/mx)) for i, v in enumerate(vals) if v is not None]
        d = " ".join(("M" if i == 0 else "L")+f"{x:.1f},{y:.1f}" for i, (x, y) in enumerate(pts))
        o.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="2" stroke-linejoin="round"/>')
        for x, y in pts:
            o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="{col}" stroke="{SURF}" stroke-width="2"/>')
        ends.append((pts[-1][0], pts[-1][1], nm))
    ends.sort(key=lambda t: t[1])
    last = -1e9
    for ex, ey, nm in ends:
        ly = max(ey+4, last+12)
        last = ly
        o.append(f'<text x="{ex+10:.1f}" y="{ly:.1f}" class="val">{esc(nm)}</text>')
    o.append("</svg>")
    return "".join(o)
