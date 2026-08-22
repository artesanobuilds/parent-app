#!/usr/bin/env python3
"""Walk a Figma /v1/files/:key/nodes JSON payload into a measured, greppable
text spec: one line per node with its position (relative to its frame's own
origin), size, fill, stroke, corner radius, typography, and auto-layout gap/
padding. This is the format every FRAME block in docs/design/*.md follows.

Usage:
    python3 tools/figma-walk.py <input.json> <output.txt>

Workflow (see docs/design/figma-fidelity-playbook.md):
  1. Fetch every frame you need in ONE batched /nodes call (budget is tight).
  2. Walk it with this script.
  3. Read the walked text per-frame as you implement — translate EVERY
     measured property (not just the gist) to a Hearth token.
  4. Append the walked FRAME blocks to the relevant docs/design/*.md file so
     the next session doesn't have to re-fetch.
"""
import json, sys

SRC = sys.argv[1]; OUT = sys.argv[2]
d = json.load(open(SRC))


def hexof(c):
    return "#%02X%02X%02X" % (round(c["r"] * 255), round(c["g"] * 255), round(c["b"] * 255))


def fills(n):
    out = []
    for f in n.get("fills", []):
        if f.get("visible", True) is False: continue
        if f.get("type") == "SOLID":
            h = hexof(f["color"]); o = f.get("opacity", 1)
            out.append(h if o == 1 else f"{h}@{o:.2f}")
        elif f.get("type", "").startswith("GRADIENT"):
            stops = ",".join(hexof(s["color"]) for s in f.get("gradientStops", []))
            out.append(f"{f['type']}({stops})")
        elif f.get("type") == "IMAGE":
            out.append("IMAGE")
    return "+".join(out)


def walk(n, frame_origin, depth, w):
    bb = n.get("absoluteBoundingBox") or {}
    x = bb.get("x", 0) - frame_origin[0]; y = bb.get("y", 0) - frame_origin[1]
    parts = [f"{'  ' * depth}{n.get('name', '?')!r} [{n.get('type')}] id={n.get('id')}",
             f"@({x:.0f},{y:.0f}) {bb.get('width', 0):.0f}x{bb.get('height', 0):.0f}"]
    if n.get("opacity", 1) != 1: parts.append(f"opacity={n['opacity']:.2f}")
    fl = fills(n)
    if fl: parts.append(f"fill={fl}")
    for s in n.get("strokes", []):
        if s.get("type") == "SOLID":
            parts.append(f"stroke={hexof(s['color'])} w={n.get('strokeWeight')}")
    if "cornerRadius" in n: parts.append(f"r={n['cornerRadius']}")
    if n.get("rectangleCornerRadii"): parts.append(f"r={n['rectangleCornerRadii']}")
    st = n.get("style")
    if st:
        parts.append(f"{st.get('fontFamily')} {st.get('fontWeight')} {st.get('fontSize')}/"
                      f"{st.get('lineHeightPx', 0):.0f} ls{st.get('letterSpacing', 0):.2f}")
        chars = (n.get("characters") or "").replace("\n", "\\n")
        parts.append(f"text={chars[:80]!r}")
    if n.get("layoutMode"):
        parts.append(f"auto={n['layoutMode']} gap={n.get('itemSpacing', 0)} "
                      f"pad=({n.get('paddingTop', 0)},{n.get('paddingRight', 0)},"
                      f"{n.get('paddingBottom', 0)},{n.get('paddingLeft', 0)})")
    w.write("  ".join(parts) + "\n")
    for c in n.get("children", []):
        walk(c, frame_origin, depth + 1, w)


with open(OUT, "w") as w:
    for nid, entry in d["nodes"].items():
        doc = entry["document"]
        bb = doc.get("absoluteBoundingBox") or {"x": 0, "y": 0}
        w.write(f"\n===== FRAME {nid} {doc.get('name')!r} =====\n")
        walk(doc, (bb["x"], bb["y"]), 0, w)
print("done")
