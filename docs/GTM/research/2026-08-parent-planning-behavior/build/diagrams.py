"""Hand-authored schematic diagrams. Same CSS custom properties as the charts,
so they follow the report's light/dark palette."""
S1, S2, S3 = "var(--series-1)", "var(--series-2)", "var(--series-3)"
INK, INK2, MUT = "var(--text-primary)", "var(--text-secondary)", "var(--text-muted)"
RULE, SURF, SOFT = "var(--rule)", "var(--surface-1)", "var(--accent-soft)"

def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
def _o(w,h): return (f'<svg class="chart diagram" viewBox="0 0 {w} {h}" role="img" '
                     f'preserveAspectRatio="xMidYMid meet" xmlns="http://www.w3.org/2000/svg">')
def box(x,y,w,h,label,sub=None,fill=SURF,stroke=RULE,dash=None,tcol=INK,r=7):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    o=[f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.4"{d}/>']
    ty = y+h/2+4 if not sub else y+h/2-3
    o.append(f'<text x="{x+w/2}" y="{ty}" text-anchor="middle" class="dlab" fill="{tcol}">{esc(label)}</text>')
    if sub: o.append(f'<text x="{x+w/2}" y="{y+h/2+13}" text-anchor="middle" class="dsub">{esc(sub)}</text>')
    return "".join(o)
def arrow(x1,y1,x2,y2,col=MUT,dash=None,head=True):
    d=f' stroke-dasharray="{dash}"' if dash else ""
    o=[f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{col}" stroke-width="1.6"{d}/>']
    if head:
        import math
        a=math.atan2(y2-y1,x2-x1); L,W=7,3.6
        p=[(x2,y2),(x2-L*math.cos(a)+W*math.sin(a), y2-L*math.sin(a)-W*math.cos(a)),
           (x2-L*math.cos(a)-W*math.sin(a), y2-L*math.sin(a)+W*math.cos(a))]
        o.append('<polygon points="'+" ".join(f"{px:.1f},{py:.1f}" for px,py in p)+f'" fill="{col}"/>')
    return "".join(o)
def wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if len(t) <= width: cur = t
        else: lines.append(cur); cur = wd
    if cur: lines.append(cur)
    return lines

def pill(x,y,text,col):
    w=6.6*len(text)+16
    return (f'<rect x="{x}" y="{y}" width="{w:.0f}" height="17" rx="8.5" fill="{col}" opacity=".14"/>'
            f'<text x="{x+w/2:.0f}" y="{y+12}" text-anchor="middle" class="dpill" fill="{col}">{esc(text)}</text>'), w

D = {}

# 1 ---------------------------------------------------------------- capture gap
w,h=760,318; o=[_o(w,h)]
o.append(f'<text x="0" y="12" class="dhead">How a parent learns something</text>')
o.append(f'<text x="330" y="12" class="dhead">How it could reach the app today</text>')
o.append(f'<text x="640" y="12" class="dhead">Works?</text>')
rows=[("Email from the school portal","Gmail sync","partial",S2,"connected accounts only, capped at 100"),
      ("Paper flyer in the backpack","Photograph it","partial",S2,"camera exists in signup only"),
      ("Text from another parent","Nothing","no",None,"cannot be forwarded on iPhone"),
      ("Told at pickup, in the car","Nothing","no",None,"no screen accepts a typed note"),
      ("Email from a camp or team","Gmail sync","partial",S2,"only for camps already saved")]
y=28
for lab,route,status,col,note in rows:
    o.append(box(0,y,300,34,lab))
    if route=="Nothing":
        o.append(arrow(304,y+17,436,y+17,col=S2,dash="4 4"))
        o.append(box(440,y,170,34,"no way in",fill="none",stroke=S2,dash="4 4",tcol=S2))
        p,_=pill(628,y+9,"blocked",S2); o.append(p)
    else:
        o.append(arrow(304,y+17,436,y+17,col=S3))
        o.append(box(440,y,170,34,route,fill=SOFT,stroke=S3))
        p,_=pill(628,y+9,"partial",S3); o.append(p)
    o.append(f'<text x="440" y="{y+47}" class="dnote">{esc(note)}</text>')
    y+=52
o.append(f'<text x="0" y="{h-8}" class="dnote">Three of the five ways a parent actually learns about an obligation have no route into the product at all.</text>')
o.append("</svg>"); D["capture-gap"]="".join(o)

# 2 --------------------------------------------------------- workflow spectrum
w,h=760,290; o=[_o(w,h)]
o.append('<text x="0" y="12" class="dhead">Summer camp: eight steps, once or twice a year</text>')
steps=["find","shortlist","decide","register","pay","forms","pack","attend"]
x=0
for i,s in enumerate(steps):
    o.append(box(x,24,84,30,s,fill=SOFT,stroke=S1))
    if i<len(steps)-1: o.append(arrow(x+85,39,x+92,39,col=MUT))
    x+=93
o.append(f'<text x="0" y="76" class="dnote">The six-stage board was built for this. The ceremony is worth it because the job is long and the deadline is fixed.</text>')
o.append(f'<line x1="0" y1="96" x2="{w}" y2="96" stroke="{RULE}"/>')
o.append('<text x="0" y="122" class="dhead">Dentist appointment: one step, about twenty-three times a year</text>')
o.append(box(0,134,84,30,"book",fill=SOFT,stroke=S3))
o.append(arrow(85,149,150,149,col=MUT))
o.append(box(154,134,230,30,"same six-stage board",fill="none",stroke=S2,dash="4 4",tcol=S2))
o.append(arrow(386,149,450,149,col=S2,dash="4 4"))
o.append(box(454,134,300,30,'card reads "all set", then hides',fill="none",stroke=S2,dash="4 4",tcol=S2))
o.append(f'<text x="0" y="186" class="dnote">Recorded honestly, a booked appointment is already finished, so the board files it as done and the parent</text>')
o.append(f'<text x="0" y="200" class="dnote">stops seeing it. The product also adds a confirmation task, turning a one-step job into a two-step one.</text>')
o.append(f'<line x1="0" y1="220" x2="{w}" y2="220" stroke="{RULE}"/>')
o.append(f'<text x="0" y="244" class="dhead">Nothing a family does is both long and frequent</text>')
o.append(f'<text x="0" y="264" class="dnote">Long jobs are rare. Frequent jobs are short. So the ceremony that makes camp work can never pay for itself</text>')
o.append(f'<text x="0" y="278" class="dnote">on the short ones, and the short ones are where most of the year lives.</text>')
o.append("</svg>"); D["workflow-spectrum"]="".join(o)

# 3 ------------------------------------------------------------------- doors
w,h=760,238; o=[_o(w,h)]
o.append('<text x="0" y="12" class="dhead">The five kinds of planning job the agent already knows how to run</text>')
doors=[("Camps and\nschool breaks","open","1 to 2 a year",S1),
       ("Weekend\noutings","open","about 39 a year",S1),
       ("Classes and\nsports","hidden","150 to 250 events",S2),
       ("School\nstuff","hidden","about 12 a year",S2),
       ("Family\ntrips","hidden","2 to 4 a year",S2)]
x=0
for lab,state,freq,col in doors:
    openp = state=="open"
    fillv = SOFT if openp else "none"
    strokev = S1 if openp else S2
    dashv = "" if openp else ' stroke-dasharray="4 4"'
    o.append(f'<rect x="{x}" y="26" width="140" height="86" rx="8" fill="{fillv}" '
             f'stroke="{strokev}" stroke-width="1.4"{dashv}/>')
    for i,line in enumerate(lab.split("\n")):
        o.append(f'<text x="{x+70}" y="{52+i*15}" text-anchor="middle" class="dlab">{esc(line)}</text>')
    p,pw = pill(x+70-((6.6*len(("visible" if openp else "hidden"))+16)/2), 84, "visible" if openp else "hidden", S1 if openp else S2)
    o.append(p)
    o.append(f'<text x="{x+70}" y="{126}" text-anchor="middle" class="dnote">{esc(freq)}</text>')
    x+=155
o.append(f'<text x="0" y="164" class="dnote">A hidden door is not missing code. The work is built and tested; a switch simply keeps its starter card off the</text>')
o.append(f'<text x="0" y="178" class="dnote">screen, so a parent never learns the product can do it. Turning one on is a configuration change.</text>')
o.append(f'<text x="0" y="206" class="dhead">The two visible doors both send a parent to a web search</text>')
o.append(f'<text x="0" y="226" class="dnote">In August, camp demand is at its floor for the year. The two doors that would carry the autumn are the hidden ones.</text>')
o.append("</svg>"); D["doors-open"]="".join(o)

# 4 -------------------------------------------------------------- email paths
w,h=760,320; o=[_o(w,h)]
o.append('<text x="0" y="12" class="dhead">Where a school or camp email travels under each option</text>')
lanes=[("A", "Gmail sign-in", [("School","parent's Gmail","the app")], S2,
        "Needs Google's approval. Until then, 100 accounts ever, and it only rechecks camps already saved."),
       ("B", "Register our address at the school", [("School","our address","the app")], S2,
        "Blocked at six of eleven platforms, including the two largest. Rejected."),
       ("B'", "Parent forwards their own mail", [("School","parent's inbox","the app")], S1,
        "One rule, set once, in the parent's own mailbox. No approval needed. Works on any provider."),
       ("C", "Both", [("School","either route","the app")], S1,
        "Widest coverage. Costs a second setup path to explain and a duplicate-message problem to solve.")]
y=30
for tag,name,flow,col,note in lanes:
    o.append(f'<circle cx="14" cy="{y+17}" r="13" fill="{col}" opacity=".16"/>')
    o.append(f'<text x="14" y="{y+21}" text-anchor="middle" class="dlab" fill="{col}">{esc(tag)}</text>')
    o.append(f'<text x="36" y="{y+13}" class="dlab">{esc(name)}</text>')
    a,b,c = flow[0]
    o.append(box(300,y,110,30,a,fill=SURF))
    o.append(arrow(412,y+15,452,y+15,col=col,dash=None if tag in ("B'","C") else "4 4"))
    o.append(box(456,y,150,30,b,fill=SOFT,stroke=col))
    o.append(arrow(608,y+15,648,y+15,col=col,dash=None if tag in ("B'","C") else "4 4"))
    o.append(box(652,y,104,30,c,fill=SURF))
    for li, line in enumerate(wrap(note, 60)[:2]):
        o.append(f'<text x="36" y="{y+29+li*13}" class="dnote">{esc(line)}</text>')
    y+=66
o.append(f'<text x="0" y="{h-8}" class="dnote">A dashed path is one that depends on someone else\'s permission. Only the parent-forward route depends on nobody.</text>')
o.append("</svg>"); D["email-paths"]="".join(o)

if __name__ == "__main__":
    import json, os
    p=os.path.join(os.path.dirname(__file__),"diagrams.json")
    json.dump(D, open(p,"w")); print("diagrams built:", ", ".join(D))
