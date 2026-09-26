import json, os, re, subprocess, sys, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "build")
charts = json.load(open(os.path.join(B, "charts.json")))
diagrams = json.load(open(os.path.join(B, "diagrams.json")))
md = open(os.path.join(ROOT, "report.md")).read()

# --- swap chart markers for placeholders -------------------------------------
found, missing = [], []
def repl(m):
    raw = m.group(1).strip()
    fn = re.split(r"[\s—–-]", raw, 1)[0].strip().strip(":")
    cap = raw[len(fn):].lstrip(" :—–-").strip()
    if fn in charts and charts[fn]:
        found.append(fn)
        return f'<div data-chart="{fn}" data-cap="{html.escape(cap, quote=True)}"></div>'
    missing.append(fn)
    return f'<p class="cap">[chart unavailable: {html.escape(fn)}]</p>'

md = re.sub(r"\[CHART:\s*([^\]]+)\]", repl, md)

dfound, dmissing = [], []
def drepl(m):
    raw = m.group(1).strip()
    m2 = re.match(r"([A-Za-z0-9_-]+)\s*(?:[-–—:]\s*)?(.*)", raw, re.S)
    key, cap = m2.group(1).strip(), m2.group(2).strip()
    if key in diagrams:
        dfound.append(key)
        return f'<div data-diagram="{key}" data-cap="{html.escape(cap, quote=True)}"></div>'
    dmissing.append(key)
    return f'<p class="cap">[diagram unavailable: {html.escape(key)}]</p>'

md = re.sub(r"\[DIAGRAM:\s*([^\]]+)\]", drepl, md)
open(os.path.join(B, "_body.md"), "w").write(md)

# --- markdown -> html --------------------------------------------------------
frag = subprocess.run(
    ["pandoc", "-f", "markdown+pipe_tables+raw_html+fenced_code_blocks-smart",
     "-t", "html5", os.path.join(B, "_body.md")],
    capture_output=True, text=True, check=True).stdout

# --- inject the rendered svg -------------------------------------------------
def inject(m):
    fn, cap = m.group(1), html.unescape(m.group(2))
    body = charts[fn]
    figcap = f'<figcaption>{cap}</figcaption>' if cap else ""
    return f'<figure class="fig" id="fig-{fn.replace(".csv","")}">{figcap}{body}<p class="src">Data: <code>data/{fn}</code></p></figure>'

DPLACE = re.compile(
    r'<div\s+data-diagram="([^"]+)"\s+data-cap="([^"]*)"\s*>\s*</div>', re.S)
def dinject(m):
    key, cap = m.group(1), html.unescape(m.group(2))
    figcap = f'<figcaption>{cap}</figcaption>' if cap else ""
    return f'<figure class="fig diagramfig" id="dia-{key}">{figcap}{diagrams[key]}</figure>'
frag, dn = DPLACE.subn(dinject, frag)
if dn != len(dfound):
    raise SystemExit(f"DIAGRAM INJECTION FAILED: placed {dn} of {len(dfound)}")

PLACEHOLDER = re.compile(
    r'<div\s+data-chart="([^"]+)"\s+data-cap="([^"]*)"\s*>\s*</div>', re.S)
frag, nsub = PLACEHOLDER.subn(inject, frag)
if nsub != len(found):
    leftover = re.findall(r'data-chart="([^"]+)"', frag)
    raise SystemExit(f"CHART INJECTION FAILED: placed {nsub} of {len(found)}; leftover={leftover}")

CSS = """
:root{
  --surface-1:#fcfcfb; --surface-2:#f6f6f4; --text-primary:#14140f; --text-secondary:#4a4a44;
  --text-muted:#77776e; --rule:#e3e3dd; --grid:#e8e8e2;
  --series-1:#2a78d6; --series-2:#eb6834; --series-3:#1baf7a;
  --accent-soft:#eef4fd;
}
@media (prefers-color-scheme: dark){ :root:not([data-theme="light"]){
  --surface-1:#16160f; --surface-2:#1e1e18; --text-primary:#f5f5ef; --text-secondary:#c6c6bb;
  --text-muted:#93938a; --rule:#33332c; --grid:#2c2c26;
  --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70; --accent-soft:#1b2433;
}}
:root[data-theme="dark"]{
  --surface-1:#16160f; --surface-2:#1e1e18; --text-primary:#f5f5ef; --text-secondary:#c6c6bb;
  --text-muted:#93938a; --rule:#33332c; --grid:#2c2c26;
  --series-1:#3987e5; --series-2:#d95926; --series-3:#199e70; --accent-soft:#1b2433;
}
*{box-sizing:border-box}
body{background:var(--surface-1); color:var(--text-primary);
  font:16px/1.62 "Charter","Iowan Old Style",Georgia,serif;
  margin:0; padding:56px 28px 96px; -webkit-font-smoothing:antialiased}
main{max-width:820px; margin:0 auto}
h1,h2,h3,h4{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,system-ui,sans-serif;
  line-height:1.22; letter-spacing:-.012em; color:var(--text-primary)}
h1{font-size:2.15rem; margin:0 0 .3em; font-weight:660}
h2{font-size:1.42rem; margin:2.7em 0 .55em; padding-top:.85em; border-top:1px solid var(--rule); font-weight:640}
h3{font-size:1.1rem; margin:1.9em 0 .4em; font-weight:640}
h4{font-size:.94rem; margin:1.7em 0 .5em; color:var(--text-secondary); font-weight:620;
   text-transform:none; letter-spacing:0}
p{margin:0 0 1.02em}
strong{font-weight:640}
a{color:var(--series-1)}
code{font:.86em/1.4 ui-monospace,SFMono-Regular,Menlo,monospace; background:var(--surface-2);
  padding:.1em .36em; border-radius:4px}
blockquote{margin:1.4em 0; padding:.75em 1.15em; border-left:3px solid var(--series-1);
  background:var(--accent-soft); border-radius:0 6px 6px 0; color:var(--text-primary)}
blockquote p:last-child{margin-bottom:0}
table{border-collapse:collapse; width:100%; margin:1.25em 0; font-size:.855rem; line-height:1.45;
  font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif}
th,td{text-align:left; padding:.46em .62em; border-bottom:1px solid var(--rule); vertical-align:top;
  hyphens:auto; overflow-wrap:anywhere}
td:first-child{font-weight:600}
th{font-weight:640; color:var(--text-secondary); font-size:.82rem; letter-spacing:.02em}
tbody tr:last-child td{border-bottom:none}
ul,ol{margin:0 0 1.02em; padding-left:1.35em}
li{margin:.3em 0}
.fig{margin:2.1em 0 2.4em; padding:1.15em 1.15em .5em; background:var(--surface-2);
  border:1px solid var(--rule); border-radius:10px; overflow:hidden; page-break-inside:avoid; break-inside:avoid}
.fig figcaption{font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif;
  font-size:.92rem; font-weight:620; margin-bottom:.9em; color:var(--text-primary)}
.fig h4{margin:1.5em 0 .6em}
svg.chart{width:100%; height:auto; display:block; overflow:visible}
svg .dhead{font:12.5px -apple-system,system-ui,sans-serif; font-weight:640; fill:var(--text-primary)}
svg .dlab{font:12px -apple-system,system-ui,sans-serif; fill:var(--text-primary)}
svg .dsub{font:10.5px -apple-system,system-ui,sans-serif; fill:var(--text-secondary)}
svg .dnote{font:10.5px -apple-system,system-ui,sans-serif; fill:var(--text-secondary)}
svg .dpill{font:10px -apple-system,system-ui,sans-serif; font-weight:640}
.diagramfig{background:transparent; border-style:dashed}
svg .lbl{font:12px -apple-system,system-ui,sans-serif; fill:var(--text-secondary)}
svg .val{font:11.5px -apple-system,system-ui,sans-serif; fill:var(--text-primary)}
svg .val.emph{font-weight:660}
svg .ax{font:11px -apple-system,system-ui,sans-serif; fill:var(--text-muted)}
svg .note{font:10.5px -apple-system,system-ui,sans-serif; fill:var(--text-muted)}
.legend{font-family:-apple-system,system-ui,sans-serif; font-size:.8rem; color:var(--text-secondary);
  margin:.2em 0 .7em; display:flex; flex-wrap:wrap; gap:.35em 1.1em}
.legend .key{display:inline-flex; align-items:center; gap:.42em}
.legend i{width:11px; height:11px; border-radius:3px; display:inline-block}
.cap,.src{font-family:-apple-system,BlinkMacSystemFont,system-ui,sans-serif;
  font-size:.83rem; line-height:1.55; color:var(--text-secondary); margin:.75em 0 .4em}
.src{font-size:.75rem; color:var(--text-muted); margin:.5em 0 .3em}
hr{border:none; border-top:1px solid var(--rule); margin:2.4em 0}
@page{size:A4; margin:17mm 15mm 19mm}
@media print{
  body{padding:0; background:#fff; font-size:10.4pt}
  table{font-size:8.6pt; line-height:1.38}
  th,td{padding:.34em .46em}
  .fig{background:#fbfbf9}
  main{max-width:none}
  h1,h2,h3,h4{break-after:avoid}
  h2{break-before:auto}
  .fig,blockquote{break-inside:avoid}
  table{break-inside:auto}
  thead{display:table-header-group}
  tr{break-inside:avoid}
  h2+p,h3+p{break-after:avoid}
  a{color:inherit; text-decoration:none}
}
"""

TITLE = "Who plans, what they plan, and how they would talk to it"
out = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{TITLE}</title><style>{CSS}</style></head>
<body><main>{frag}</main></body></html>"""

open(os.path.join(ROOT, "report.html"), "w").write(out)
print(f"charts placed: {len(found)} | diagrams placed: {len(dfound)} {sorted(set(dfound))}")
if dmissing: print("MISSING DIAGRAMS:", sorted(set(dmissing)))
if missing: print("MISSING MARKERS:", sorted(set(missing)))
print("report.html bytes:", len(out))
