import csv, os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import svg
from svg import S1, S2, S3, hbar, grouped, legend, scatter, heatmap, lines

D = os.path.join(os.path.dirname(__file__), "..", "data")
def rd(f):
    with open(os.path.join(D, f)) as fh: return list(csv.DictReader(fh))
def num(v, d=None):
    try: return float(str(v).replace(",", ""))
    except Exception: return d

C = {}

# 1 — cohort population
r = [x for x in rd("cohort_population.csv") if x["cohort"] not in ("ALL parent households",)]
C["cohort_population.csv"] = (
    legend([("Share of US parent households", S1)]) +
    hbar([(f'{x["cohort"]} ({x["age_in_2026"]})', num(x["share_pct"]), S1,
           f'· {num(x["parent_households_millions"]):.2f}M') for x in r],
         fmt="{:.1f}%", note="US Census Table F1 (2023), recomputed on 2026 age bands · Tier A-derived · n≈60,000 addresses") +
    "<h4>…and their children's ages — the reason parent generation is the wrong product axis</h4>" +
    legend([("Has a child under 6", S1), ("Has a child 6–11", S2), ("Has a child 12–17", S3)]) +
    grouped([x["cohort"].replace(" and older","") for x in r if x["pct_with_child_under_6"]],
            [("under 6",[num(x["pct_with_child_under_6"]) for x in r if x["pct_with_child_under_6"]],S1),
             ("6–11",[num(x["pct_with_child_6_11"]) for x in r if x["pct_with_child_under_6"]],S2),
             ("12–17",[num(x["pct_with_child_12_17"]) for x in r if x["pct_with_child_under_6"]],S3)],
            fmt="{:.0f}%", ymax=100, pad_t=30, ylab="% of cohort"))

# 2 — planning labour by employment
r = rd("planning_labor_by_employment.csv")
def pick(sub):
    for x in r:
        if sub.lower() in x["population"].lower() and "HEADLINE" in x["series"]: return x
    for x in r:
        if sub.lower() in x["population"].lower(): return x
emp = [x for x in r if x["series"].startswith("HEADLINE")]
alp = [x for x in r if x["series"].startswith("Secondary")][:3]
cats = ["All parents\nof a child <18", "Youngest\nchild 6–17", "Youngest\nchild <6"]
C["planning_labor_by_employment.csv"] = (
    legend([("Mothers", S1), ("Fathers", S2)]) +
    grouped(["Employed, child <18", "Employed, youngest 6–17", "All parents, youngest 6–17"],
            [("Mothers", [num(emp[0]["mothers_min_per_day"]), num(emp[1]["mothers_min_per_day"]),
                          num(alp[1]["mothers_min_per_day"])], S1),
             ("Fathers", [num(emp[0]["fathers_min_per_day"]), num(emp[1]["fathers_min_per_day"]),
                          num(alp[1]["fathers_min_per_day"])], S2)],
            fmt="{:.1f}", pad_t=30, ylab="minutes/day") +
    '<p class="cap">The buyer is employed. Among employed parents the gap is <strong>1.75×</strong> '
    '(8.4 vs 4.8 min/day) — not the <strong>3.0×</strong> that the all-parents figure reports, which is '
    'levered by non-employed mothers. BLS ATUS 2025, Tables 8A/8B, Tier A. '
    'BLS suspended collection 1 Oct – 12 Nov 2025; 2025 averages are 11-month and BLS states the effect '
    '“cannot be quantified.”</p>')

# 3 — obligations per year
r = [x for x in rd("obligations_per_year.csv") if num(x["two_kid_family_per_year"]) and
     not x["line_item"].upper().startswith(("TOTAL","FLOOR","BAND","SOURCED"))]
r.sort(key=lambda x: -num(x["two_kid_family_per_year"]))
C["obligations_per_year.csv"] = (
    legend([("In the sourced-only floor", S1), ("Best estimate, conditional or estimated input", S2)]) +
    hbar([(x["line_item"], num(x["two_kid_family_per_year"]),
           S1 if x["in_sourced_only_floor"].strip().upper() == "YES" else S2,
           "" if x["scheduled"].strip().upper() == "YES" else "· unscheduled")
          for x in r], fmt="{:.2f}",
         note="Obligations per year, 2-kid family · best estimate ~23 (band 20–26) · sourced-only floor ~15.06") +
    '<p class="cap">Emergency and urgent-care visits are <em>unscheduled by definition</em> and are excluded '
    'from any figure labelled “scheduled”. NCES publishes the school-meetings mean as a rounded integer (6), '
    'so decimals here are false precision — the band, not the point estimate, is the finding.</p>')

# 4 — job quadrants (central chart)
r = [x for x in rd("job_quadrants.csv") if x.get("plot","true").strip().lower() == "true"]
SHORT = {
    "School event (parent-attended)": "School event",
    "School-break coverage (non-summer)": "Break coverage",
    "Therapy / orthodontia session": "Therapy / ortho",
    "Fall/spring activity registration": "Activity registration",
    "Weekly sports logistics": "Weekly sports logistics",
    "Immunization deadline": "Immunisation",
    "ED / urgent care": "ED / urgent care",
    "Well-child visit": "Well-child",
    "Birthday party hosted": "Birthday hosted",
    "Sports physical": "Sports physical",
    "Dental recall": "Dental recall",
    "Family trip": "Family trip",
    "Weekend outing": "Weekend outing",
    "Summer camp": "Summer camp",
}
pts = []
for x in r:
    n, f = num(x["N_steps_per_episode"]), num(x["annual_frequency_per_family"])
    if n is None or f is None: continue
    deep = n >= 4
    sports = "sports logistics" in x["job"].lower()
    pts.append((n, f, SHORT.get(x["job"], x["job"]), S2 if sports else (S1 if deep else S3),
                13 if sports else 8, sports))
C["job_quadrants.csv"] = (
    legend([("Deep / episodic (Q1)", S1), ("Shallow / recurring (Q2–Q3)", S3),
            ("Weekly sports logistics — one row, 200 of 264", S2)]) +
    scatter(pts, xlab="steps per episode  →  workflow depth (N)",
            ylab="episodes per family per year (log)") +
    '<p class="cap">The deep-and-frequent quadrant (top right) is empty — depth and repetition are '
    'anti-correlated, so workflow ceremony can never be amortised. But the shallow total is dominated by a '
    'single row: <strong>weekly sports logistics is 200 of 264</strong>, and by the model’s own definition '
    'those are <em>attendances</em>, not captures. Excluding it, the honest comparison is '
    '<strong>~23 obligations/yr vs ~16 deep objects — parity, not an order of magnitude</strong>.</p>')

# 5 — seasonality heatmap + volume
r = rd("seasonality_month_x_task.csv")
months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
rows = [x["task_family"] for x in r]
cells = [[int(num(x[m], 0)) for m in months] for x in r]
vols = [(x["task_family"], num(x["shared_scale_volume"], 0), S1) for x in r]
vols.sort(key=lambda t: -t[1])
C["seasonality_month_x_task.csv"] = (
    heatmap(rows, months, cells,
            note="Intensity 0–3 · Google Trends, geo=US, 2021-08→2026-08 · Tier C (raw feed, no disclosed n)") +
    "<h4>Flatness is not demand — the same task families on a shared volume scale</h4>" +
    hbar(vols, fmt="{:.2f}",
         note="Search volume indexed to “summer camp” = 36.6 on a shared scale") +
    '<p class="cap">Summer camp’s <em>worst</em> month exceeds dental’s <em>best</em> by roughly 4.5×. A flat '
    'curve is steady, not large. Two caveats travel with this chart: fall registration’s volume is almost '
    'entirely a browse term (<code>after school program</code>), and school admin’s 30.7 is '
    '<code>back to school</code>, a retail term. Google Trends is not parent-scoped.</p>')

# 6 — camp forward search
r = rd("camp_forward_search.csv")
cyc = {}
for x in r: cyc.setdefault(x["cycle"], []).append(x)
ser = []
for i, (k, v) in enumerate(sorted(cyc.items())):
    v.sort(key=lambda z: int(num(z["month_order"], 0)))
    ser.append((k.split(" (")[0].replace("summer camp ", "cycle "), [num(z["index_value"], 0) for z in v], [S1, S2][i % 2]))
xl = [z["month"] for z in sorted(list(cyc.values())[0], key=lambda z: int(num(z["month_order"], 0)))]
C["camp_forward_search.csv"] = (
    lines(xl, ser) +
    '<p class="cap">Next-summer camp search roughly <strong>doubles in November, doubles again in December '
    'and triples into January</strong> — reproduced exactly across two independent cycles by a second '
    'verifier. <strong>The dead window is August–October: three months, not six.</strong> That hole is filled '
    'by two verticals already built and flagged off.</p>')

# 7 — activity supply by metro
r = [x for x in rd("activity_supply_by_metro.csv")
     if num(x.get("providers_within_25mi")) and num(x.get("live_sessions_within_25mi"))]
r.sort(key=lambda x: -num(x["providers_within_25mi"]))
r = r[:10]
C["activity_supply_by_metro.csv"] = (
    legend([("Providers within 25 mi", S1), ("Live sessions within 25 mi", S2)]) +
    grouped([x["geography"] for x in r],
            [("Providers", [num(x["providers_within_25mi"]) for x in r], S1),
             ("Live", [num(x["live_sessions_within_25mi"]) for x in r], S2)],
            fmt="{:.0f}", h=330) +
    '<p class="cap">Original measurement of ActivityHero’s public search index (2026-08-21, reproduced '
    'independently 2026-08-22). Nationally only <strong>9,008 of 94,848 sessions (9.5%) are live</strong>. '
    'But provider rank and live rank <em>disagree</em>: LA has more providers than SF (5,686 vs 4,299) and a '
    'third the live sessions. An August pull is a seasonal trough — year-round classes survive it, summer-only '
    'supply does not — so this is a single-timepoint measurement, not a structural gradient. '
    'Vendor credential withheld per ActivityHero’s terms.</p>')

# 8 — voice adoption by cohort
r = rd("voice_adoption_by_cohort.csv")
bands = ["18-29", "30-49", "50-64", "65+"]
def series_for(metric):
    d = {x["age_band"]: num(x["value_pct"]) for x in r if x["metric"].strip().lower() == metric.lower()}
    return [d.get(b) for b in bands]
mets = sorted({x["metric"] for x in r})
pick3 = [m for m in ["Smart-speaker ownership", "AI chatbot use - ever", "AI chatbot use - daily"] if m in mets]
cols = [S1, S2, S3]
C["voice_adoption_by_cohort.csv"] = (
    legend([(m.replace(" - ", " — "), cols[i]) for i, m in enumerate(pick3)]) +
    grouped(bands, [(m, series_for(m), cols[i]) for i, m in enumerate(pick3)],
            fmt="{:.0f}%", ymax=80, pad_t=30, ylab="% of age band") +
    '<p class="cap">Both peak at <strong>30–49</strong> — the core parent cohort — and 18–29 is '
    '<em>second-lowest</em> on smart-speaker ownership. The intuition that younger parents are the voice '
    'audience is not supported. Pew Research Center, n=5,119 US adults, fielded 17–23 Feb 2026, Tier B.</p>')

# 9 — email options scoring
r = [x for x in rd("email_options_scoring.csv") if num(x.get("weight"))]
opts = [c for c in r[0].keys() if c.lower().startswith(("a_", "b_", "c_", "score_"))] if r else []
C["email_options_scoring.csv"] = ""
try:
    keys = [k for k in r[0].keys() if k.startswith("score_")]
    tot = {k: 0.0 for k in keys}
    for x in r:
        w = num(x["weight"], 0)
        for k in keys:
            v = num(x[k]); 
            if v is not None: tot[k] += v*w
    order = sorted(tot.items(), key=lambda t: -t[1])
    nice = {"A_gmail_oauth": "A — Gmail OAuth", "B_register_our_address": "B — register our address",
            "Bprime_parent_autoforward": "B′ — parent-side auto-forward", "C_A_plus_Bprime": "C — both (A + B′)"}
    C["email_options_scoring.csv"] = (
        hbar([(nice.get(k.replace("score_", "").strip(), k), v,
               S1 if "prime" in k.lower() else S2)
              for k, v in order], fmt="{:.1f}",
             note="Weighted score, max 77.5 · B′ re-scored 63.5 after the auto-confirm unlock was falsified") +
        '<p class="cap">B′ and C both far outrank shipping Gmail OAuth alone. The ranking survived the '
        'correction; the original headline (69.5) did not — Google still requires the user to return and click '
        'Save Changes, and shows a week-long “someone else may have access to your account” banner precisely '
        'when B′’s pitch is trustworthiness.</p>')
except Exception as e:
    C["email_options_scoring.csv"] = f'<p class="cap">[scoring chart unavailable: {e}]</p>'


# 10 — channel by cohort
r = rd("channel_by_cohort.csv")
C["channel_by_cohort.csv"] = (
    legend([("Gen Z parents (18-29)", S1), ("Millennial (30-45)", S2), ("Gen X (46-61)", S3)]) +
    grouped([x["channel"] for x in r],
            [("Gen Z", [num(x["gen_z_18_29"]) for x in r], S1),
             ("Millennial", [num(x["millennial_30_45"]) for x in r], S2),
             ("Gen X", [num(x["gen_x_46_61"]) for x in r], S3)],
            fmt="{:.0f}%", ymax=100, h=330, pad_t=30, ylab="% of age band") +
    '<p class="cap">Two facts do the work here. <strong>YouTube is the only near-parity channel</strong> '
    '(95/92/85), so it is the single-asset play. And <strong>Facebook inverts</strong>: it reaches Millennial '
    'and Gen X parents better than Gen Z ones, which is the opposite of the usual assumption about parent '
    'groups. Pew, n=5,119, fielded 17-23 Feb 2026, Tier B. Pew age bands are 18-29 / 30-49 / 50-64 and map '
    'only approximately to the cohort bands used elsewhere in this report.</p>')

# 11 — resonance ranking
r = rd("resonance_ranking.csv")
C["resonance_ranking.csv"] = (
    legend([("Already built, wholly or partly", S1), ("Not built", S2)]) +
    hbar([(x["move"], num(x["evidence_strength_score"]),
           S1 if x["already_built"].strip() in ("yes","partial") else S2,
           "· " + x["already_built"]) for x in r],
         fmt="{:.0f}/5",
         note="Ranked by strength of evidence that users want it, not by value or effort") +
    '<p class="cap">Rank order follows the evidence, not judgement. Four of the top five are already built '
    'in whole or in part and are either buried, flag-gated, or scoped to one screen. That is the cheapest '
    'class of move available. The weakest-evidenced item, conversational voice, is the one the product '
    'currently ships most prominently.</p>')

out = os.path.join(os.path.dirname(__file__), "charts.json")
json.dump(C, open(out, "w"))
print("charts built:", len([k for k, v in C.items() if v]), "of", len(C))
for k, v in C.items(): print(f"  {'OK ' if v else 'EMPTY'} {k}  ({len(v)} bytes)")
