"""Reproduce five README figures as editable SVG and high-resolution PNG.

Requires Python 3 and rsvg-convert (librsvg). No network or model calls.
"""
from html import escape
from pathlib import Path
import subprocess

OUT = Path(__file__).parent / "assets"
INK, MUTED = "#193341", "#536775"
TEAL, TEAL_BG = "#147C72", "#E8F4EF"
RUST, RUST_BG = "#B45C45", "#FAEEE7"
BLUE, BLUE_BG = "#3D689A", "#EDF3FA"
BORDER = "#DCE3E3"


def text(x, y, value, size=25, color=INK, weight=450, anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
            f'font-weight="{weight}" text-anchor="{anchor}">{escape(value)}</text>')


def rect(x, y, w, h, fill="white", stroke=BORDER, radius=16, dashed=False):
    dash = ' stroke-dasharray="7 6"' if dashed else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.5"{dash}/>')


def node(x, y, w, h, title, detail=None, fill="white", accent=BLUE, size=25):
    out = rect(x, y, w, h, fill)
    out += f'<rect x="{x}" y="{y+16}" width="4" height="{h-32}" rx="2" fill="{accent}"/>'
    if detail:
        out += text(x+20, y+36, title, size, INK, 650)
        for i, line in enumerate(detail):
            out += text(x+20, y+68+i*30, line, 23, MUTED)
    else:
        out += text(x+w/2, y+h/2+9, title, size, INK, 650, "middle")
    return out


def line(points, color=TEAL, dashed=False, arrow=True):
    path = "M" + " L".join(f"{x},{y}" for x, y in points)
    dash = ' stroke-dasharray="7 6"' if dashed else ""
    marker = f' marker-end="url(#{"rust" if color == RUST else "blue" if color == BLUE else "teal"})"' if arrow else ""
    return f'<path d="{path}" fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round"{dash}{marker}/>'


def label(x, y, value, good=False, width=150):
    color, bg = (TEAL, TEAL_BG) if good else (RUST, RUST_BG)
    return rect(x, y, width, 34, bg, bg, 17) + text(x+width/2, y+24, value, 17, color, 750, "middle")


def start(index, title, subtitle, before, after, note):
    desc = f"Before: {before}. After: {after}. {note}"
    out = (f'<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="820" '
           f'viewBox="0 0 1500 820" role="img" aria-labelledby="title desc">'
           f'<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc><defs>')
    for name, color in [("teal", TEAL), ("rust", RUST), ("blue", BLUE)]:
        out += (f'<marker id="{name}" viewBox="0 0 10 10" refX="9" refY="5" '
                f'markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0 L10 5 L0 10z" fill="{color}"/></marker>')
    out += '</defs><rect width="1500" height="820" fill="#F6F7F4"/><g font-family="Inter, Helvetica Neue, Arial, sans-serif">'
    out += text(48, 47, "MVP  /  HARNESS ENGINEERING", 18, TEAL, 750)
    out += text(48, 102, title, 43, INK, 750)
    out += text(48, 143, subtitle, 24, MUTED)
    out += text(1450, 104, f"0{index}", 78, "#D0DEDA", 750, "end")
    for x, good, heading in [(48, False, before), (772, True, after)]:
        out += rect(x, 183, 680, 552, "white", BORDER, 24)
        out += label(x+28, 207, "AFTER" if good else "BEFORE", good, 100)
        out += text(x+28, 280, heading, 29, INK, 700)
    out += text(48, 785, note, 22, MUTED)
    return out


def save(name, svg):
    OUT.mkdir(exist_ok=True)
    path = OUT / f"{name}.svg"
    path.write_text(svg + "</g></svg>\n")
    subprocess.run(["rsvg-convert", "--width", "2250", "--output", str(OUT/f"{name}.png"), str(path)], check=True)
    print(name)


def main():
    s = start(1, "Shared execution, distinct policies", "Consolidate lifecycle mechanics while keeping each surface's behavior.",
              "Each surface owns its own loop", "One service owns the lifecycle",
              "REST and SSE contracts stay compatible. Surface-specific safety and presentation stay separate.")
    for x, title in [(80, "Chat"), (294, "Voice"), (508, "Onboarding")]:
        s += node(x, 315, 184, 62, title, fill=BLUE_BG, size=23)
        s += line([(x+92, 377), (x+92, 418)], RUST)
        s += node(x, 426, 184, 143, "Own loop", ["Repair / retry", "Stream / save"], RUST_BG, RUST, 24)
        s += line([(x+92, 569), (x+92, 614)], RUST)
    s += node(80, 623, 612, 67, "Existing graphs", fill=BLUE_BG)
    for x, title in [(804, "Chat"), (1018, "Voice"), (1232, "Onboarding")]:
        s += node(x, 315, 184, 62, title, fill=BLUE_BG, size=23)
        s += line([(x+92, 377), (x+92, 405), (1110, 405)], TEAL, arrow=False)
    s += line([(1110, 405), (1110, 424)])
    s += node(804, 432, 612, 135, "Shared execution service", ["Own turn → repair → execute → finalize", "Adapters + per-surface policies"], TEAL_BG, TEAL, 28)
    s += line([(1110, 567), (1110, 614)])
    s += node(804, 623, 612, 67, "Existing graphs", fill=BLUE_BG)
    save("refactor-01-shared-execution", s)

    s = start(2, "Durable before done", "Agent-turn completion follows durable finalization.",
              "Success could outrun persistence", "Persistence gates success",
              "Tokens still stream incrementally. Failed finalization withholds the successful completion marker.")
    for x, good in [(108, False), (832, True)]:
        col = TEAL if good else RUST
        s += node(x, 318, 560, 74, "Stream response tokens", fill=BLUE_BG)
        s += line([(x+280, 392), (x+280, 430)], col)
        s += node(x, 440, 560, 84, "Commit final transcript" if good else "Send [DONE] to client",
                  fill=TEAL_BG if good else RUST_BG, accent=col)
        s += line([(x+280, 524), (x+280, 597)], col, dashed=not good)
        if not good:
            s += rect(x+80, 544, 400, 35, RUST_BG, RUST_BG, 10)
            s += text(x+280, 570, "DISCONNECT / CRASH WINDOW", 19, RUST, 750, "middle")
        else:
            s += label(x+188, 544, "COMMITTED", True, 184)
        s += node(x, 607, 560, 73, "Send [DONE] to client" if good else "Save transcript afterward",
                  fill=TEAL_BG if good else "white", accent=col)
    save("refactor-02-durable-completion", s)

    s = start(3, "Idempotent database effects under replay", "Recover a committed result instead of repeating the same mutation.",
              "A missing result leaves ambiguity", "A receipt proves what committed",
              "Same tenant + thread + checkpointed call ID; command and arguments must match. External effects need separate guarantees.")
    s += node(80, 316, 248, 82, "Tool call K", fill=BLUE_BG)
    s += line([(328, 357), (420, 357)], RUST)
    s += node(430, 316, 262, 82, "DB write commits", fill=RUST_BG, accent=RUST, size=24)
    s += line([(561, 398), (561, 442)], RUST)
    s += node(80, 450, 612, 100, "Process stops", ["Tool-result checkpoint is still missing"], RUST_BG, RUST)
    s += line([(204, 550), (204, 594)], RUST)
    s += node(80, 604, 248, 76, "Replay call K", fill=BLUE_BG, size=24)
    s += line([(328, 642), (420, 642)], RUST, dashed=True)
    s += node(430, 604, 262, 76, "Duplicate write?", fill=RUST_BG, accent=RUST, size=24)
    s += rect(804, 316, 612, 169, TEAL_BG, "#A9CFC4", 18)
    s += text(826, 351, "ONE DUCKDB TRANSACTION", 19, TEAL, 750)
    s += node(826, 376, 255, 78, "Business mutation", accent=TEAL, size=23)
    s += text(1110, 425, "+", 32, TEAL, 650, "middle")
    s += node(1137, 376, 257, 78, "Receipt K + result", accent=TEAL, size=23)
    s += text(1110, 522, "Crash before the graph checkpoint?", 23, MUTED, anchor="middle")
    s += line([(1110, 538), (1110, 566)])
    s += node(804, 576, 612, 114, "Replay K → return recorded result", ["Restore the missing tool result; do not write again"], TEAL_BG, TEAL, 26)
    save("refactor-03-idempotent-effects", s)

    s = start(4, "Own the turn. Fence the family.", "Coordinate overlapping work and keep deleted data from coming back.",
              "Requests can cross each other", "Ownership + deletion fences",
              "Ownership is process-local. Deletion fences reject stale generations; this is not a distributed lock.")
    s += node(80, 316, 248, 74, "Turn A", fill=BLUE_BG)
    s += node(444, 316, 248, 74, "Turn B", fill=BLUE_BG)
    s += line([(204, 390), (204, 423), (386, 423), (386, 452)], RUST)
    s += line([(568, 390), (568, 423), (386, 423)], RUST, arrow=False)
    s += node(165, 460, 442, 77, "Same conversation state", fill=RUST_BG, accent=RUST)
    s += node(80, 597, 270, 82, "Delete family", fill=RUST_BG, accent=RUST)
    s += line([(350, 638), (409, 638)], RUST, dashed=True)
    s += node(419, 584, 273, 108, "Late write", ["Data can reappear"], RUST_BG, RUST)
    s += node(804, 316, 190, 78, "A then B", fill=BLUE_BG)
    s += line([(994, 355), (1043, 355)])
    s += node(1053, 316, 363, 78, "Conversation gate", fill=TEAL_BG, accent=TEAL)
    s += text(804, 448, "FAMILY DELETION", 18, TEAL, 750)
    for y, title in [(470, "1  Close admission, then drain"),
                     (575, "2  Advance generation + delete")]:
        s += node(804, y, 612, 77, title, fill=TEAL_BG, accent=TEAL, size=25)
        if y == 470:
            s += line([(1110, 547), (1110, 565)])
    s += text(804, 684, "After cascade: evict caches; purge checkpoints.", 22, MUTED)
    s += text(804, 422, "Turns serialize within the same conversation.", 22, MUTED)
    s += text(804, 714, "Refresh snapshots; retry pending cleanup.", 22, MUTED)
    save("refactor-04-ownership-and-fences", s)

    s = start(5, "Bound the work and the retained state", "Make job lifetime, late writes and cache growth explicit.",
              "Limits were incomplete", "Bounded attempts and caches",
              "Canceling a coroutine does not kill a synchronous thread or guarantee that provider billing stops.")
    s += node(80, 316, 612, 122, "Background work", ["Cancellation / timeout did not consistently", "fence late results from unfinished work"], RUST_BG, RUST)
    s += line([(170, 469), (600, 469)], RUST, dashed=True)
    s += text(386, 508, "Work can outlive the request", 24, RUST, 600, "middle")
    s += text(80, 558, "RETAINED GRAPHS / CONNECTIONS", 18, RUST, 750)
    for i in range(7):
        s += rect(85+i*78, 587-i*3, 65, 65+i*3, RUST_BG, "#DFBEB1", 8)
    s += text(80, 700, "Growth without a consistent eviction policy", 23, MUTED)
    s += node(804, 316, 612, 127, "Background job attempt", ["Deadline + heartbeat + attempt identity", "Canceled / expired attempts cannot publish late"], TEAL_BG, TEAL)
    s += text(804, 492, "BOUNDED GRAPH CACHE", 18, TEAL, 750)
    for i in range(5):
        s += rect(810+i*86, 520, 72, 68, TEAL_BG, "#B4D8CA", 8)
        s += text(846+i*86, 563, str(i+1), 24, TEAL, 600, "middle")
    s += line([(1255, 554), (1394, 554)])
    s += text(1328, 601, "Evict LRU", 22, TEAL, 600, "middle")
    s += node(804, 632, 612, 67, "Reuse schema-compatible checkpoint connections", fill=BLUE_BG, size=23)
    save("refactor-05-bounded-resources", s)


if __name__ == "__main__":
    main()
