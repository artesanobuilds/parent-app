#!/usr/bin/env python3
"""
Build the MVP investor deck.

Every token below was measured out of Heather's original slide
(`Copy of MVP-Deck-Miguel slide TECH info .pptx`) by reading the raw
DrawingML, so this deck sits on her grid EMU-for-EMU rather than
approximating it. Copy lives in `narrative.md`; this file is the renderer.

Run:  <venv>/bin/python pitch/build_deck.py
"""

from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.util import Emu, Pt

HERE = Path(__file__).parent
ASSETS = HERE.parent / "mvp-backend" / "parent-dashboard" / "public" / "docs-assets"
OUT = HERE / "MVP-Investor-Deck.pptx"

# ---------------------------------------------------------------- tokens
# Measured from the source deck. Do not "clean these up" — they are the grid.
W, H = 18288000, 10287000

BG        = RGBColor(0xF5, 0xF0, 0xEA)   # slide ground (from slideMaster bg)
CARD      = RGBColor(0xFC, 0xFB, 0xF8)   # card fill
INK       = RGBColor(0x28, 0x20, 0x19)   # headline + card label
BODY      = RGBColor(0x6E, 0x64, 0x55)   # card body
MUTED     = RGBColor(0x9A, 0x90, 0x80)   # footer
TEAL      = RGBColor(0x1B, 0x74, 0x98)   # eyebrow label
TEAL_ALT  = RGBColor(0x1D, 0x7F, 0xA6)   # eyebrow tick

# dark-slide variants, same family
DARK_BG   = RGBColor(0x28, 0x20, 0x19)
DARK_CARD = RGBColor(0x33, 0x2A, 0x22)
DARK_INK  = RGBColor(0xFC, 0xFB, 0xF8)
DARK_BODY = RGBColor(0xC4, 0xBA, 0xAB)
DARK_TEAL = RGBColor(0x5F, 0xB4, 0xD4)   # teal lifted for AA on ink ground

DISPLAY, TEXT, MONO = "Fraunces", "Inter", "JetBrains Mono"

MARGIN      = 1143000
CONTENT_W   = W - 2 * MARGIN              # 16002000
TICK        = (MARGIN, 1045369, 533400, 38100)
EYEBROW_POS = (1847850, 914400, 4000000, 338138)
TITLE_Y     = 1595450
FOOTER_Y    = 9567863

CARD_PAD_X  = 362325
CARD_PAD_T  = 373843
LABEL_H     = 381000
BODY_GAP    = 476250                      # label_y -> body_y
GAP         = 256050
RADIUS      = 0.045                       # roundRect adjustment

SZ_TITLE, SZ_LABEL, SZ_BODY, SZ_MONO = 54, 22.5, 19.5, 18

TOTAL_SLIDES = 16


# ------------------------------------------------------------- primitives
def cols(n, width=CONTENT_W, left=MARGIN):
    """Even n-column grid across the content width."""
    w = (width - (n - 1) * GAP) // n
    return [(left + i * (w + GAP), w) for i in range(n)]


def textbox(slide, x, y, w, h, anchor=MSO_ANCHOR.TOP):
    box = slide.shapes.add_textbox(Emu(x), Emu(y), Emu(w), Emu(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = anchor
    return tf


def write(tf, text, font, size, color, bold=False, italic=False,
          spacing=1.0, space_after=0, align=PP_ALIGN.LEFT, first=True):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.line_spacing = spacing
    p.space_after = Pt(space_after)
    p.alignment = align
    r = p.add_run()
    r.text = text
    r.font.name = font
    r.font.size = Pt(size)
    r.font.bold = bold
    r.font.italic = italic
    r.font.color.rgb = color
    return p


def rect(slide, x, y, w, h, fill, shape=MSO_SHAPE.RECTANGLE, radius=None):
    s = slide.shapes.add_shape(shape, Emu(x), Emu(y), Emu(w), Emu(h))
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    s.line.fill.background()
    s.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        s.adjustments[0] = radius
    return s


# ------------------------------------------------------------- components
def new_slide(prs, dark=False):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    rect(slide, 0, 0, W, H, DARK_BG if dark else BG)
    return slide


def eyebrow(slide, text, dark=False):
    x, y, w, h = TICK
    rect(slide, x, y, w, h, DARK_TEAL if dark else TEAL_ALT)
    ex, ey, ew, eh = EYEBROW_POS
    tf = textbox(slide, ex, ey, ew, eh)
    write(tf, text.upper(), MONO, SZ_MONO, DARK_TEAL if dark else TEAL)


def wrapped_lines(text, size, width, char_ratio=0.54):
    """Estimate rendered line count. Fraunces bold averages ~0.54 em per glyph."""
    per_line = max(1, int(width / (size * 12700 * char_ratio)))
    total = 0
    for line in text.split("\n"):
        total += max(1, -(-len(line) // per_line))
    return total


def title(slide, text, size=SZ_TITLE, y=TITLE_Y, w=None, dark=False, color=None):
    """Draw the display title. Returns the y of its baseline bottom so callers
    can place the next block underneath it instead of guessing."""
    w = w or CONTENT_W
    lines = wrapped_lines(text, size, w)
    line_h = size * 12700 * 1.20
    h = int(line_h * lines) + 80000
    tf = textbox(slide, MARGIN, y, w, h)
    for i, line in enumerate(text.split("\n")):
        write(tf, line, DISPLAY, size, color or (DARK_INK if dark else INK),
              bold=True, spacing=1.08, first=(i == 0))
    slide._title_bottom = y + h
    return y + h


def below(slide, y, pad=400000):
    """Never let a block land on top of a title that wrapped further than planned."""
    return max(y, getattr(slide, "_title_bottom", 0) + pad)


def paragraph(slide, text, y, w=None, size=SZ_LABEL, dark=False, color=None):
    w = w or int(CONTENT_W * 0.78)
    y = below(slide, y)
    lines = wrapped_lines(text, size, w, char_ratio=0.47)
    h = int(size * 12700 * 1.35 * lines) + 60000
    tf = textbox(slide, MARGIN, y, w, h)
    write(tf, text, TEXT, size, color or (DARK_BODY if dark else BODY), spacing=1.35)
    slide._body_bottom = y + h
    return y + h


def cards(slide, items, y, h, n=None, dark=False, left=MARGIN, width=CONTENT_W,
          label_size=SZ_LABEL, body_size=SZ_BODY):
    """items = [(label, body), ...] on an n-column grid.

    Cards size themselves to their contents: a label that wraps to two lines
    pushes its own body down, and the row grows to fit the tallest card.
    Returns the row's bottom edge so the next row can chain off it.
    """
    n = n or len(items)
    y = max(y, getattr(slide, "_body_bottom", 0) + 240000, below(slide, 0))
    grid = cols(n, width, left)

    label_line = label_size * 12700 * 1.26
    body_line = body_size * 12700 * 1.40
    metrics = []
    for (label, text), (x, w) in zip(items, grid):
        inner_w = w - 2 * CARD_PAD_X
        l_lines = wrapped_lines(label, label_size, inner_w, 0.58)
        b_lines = wrapped_lines(text, body_size, inner_w, 0.47)
        l_h = int(label_line * l_lines)
        body_off = CARD_PAD_T + l_h + 140000
        metrics.append((inner_w, l_h, body_off, int(body_line * b_lines)))
    h = max(h, max(off + bh + 300000 for _, _, off, bh in metrics))

    for (label, text), (x, w), (inner_w, l_h, body_off, b_h) in zip(items, grid, metrics):
        rect(slide, x, y, w, h, DARK_CARD if dark else CARD,
             MSO_SHAPE.ROUNDED_RECTANGLE, RADIUS)
        tf = textbox(slide, x + CARD_PAD_X, y + CARD_PAD_T, inner_w, l_h + 40000)
        write(tf, label, TEXT, label_size, DARK_INK if dark else INK,
              bold=True, spacing=1.15)
        tf = textbox(slide, x + CARD_PAD_X, y + body_off, inner_w, b_h + 40000)
        write(tf, text, TEXT, body_size, DARK_BODY if dark else BODY, spacing=1.32)
    slide._row_bottom = y + h
    return y + h


def stat_cards(slide, items, y, h, dark=False):
    """items = [(bignum, label, source|None), ...]"""
    y = max(y, getattr(slide, "_body_bottom", 0) + 240000, below(slide, 0))
    grid = cols(len(items))
    num_h = 1250000
    needed = []
    for (num, label, src), (x, w) in zip(items, grid):
        inner_w = w - 2 * CARD_PAD_X
        lh = wrapped_lines(label, SZ_BODY, inner_w, 0.47) * SZ_BODY * 12700 * 1.30
        sh = (wrapped_lines(src, 12.5, inner_w, 0.60) * 12.5 * 12700 * 1.30 + 120000) if src else 0
        needed.append(CARD_PAD_T + num_h + int(lh) + int(sh) + 300000)
    h = max(h, max(needed))

    for (num, label, src), (x, w) in zip(items, grid):
        rect(slide, x, y, w, h, DARK_CARD if dark else CARD,
             MSO_SHAPE.ROUNDED_RECTANGLE, RADIUS)
        inner_w = w - 2 * CARD_PAD_X
        tf = textbox(slide, x + CARD_PAD_X, y + CARD_PAD_T - 40000, inner_w, num_h)
        write(tf, num, DISPLAY, 68, DARK_TEAL if dark else TEAL, bold=True, spacing=1.0)
        tf = textbox(slide, x + CARD_PAD_X, y + CARD_PAD_T + num_h - 60000,
                     inner_w, h - CARD_PAD_T - num_h)
        write(tf, label, TEXT, SZ_BODY, DARK_INK if dark else INK, spacing=1.30)
        if src:
            write(tf, src, MONO, 12.5, MUTED, spacing=1.30, space_after=0, first=False)
    return y + h


def footer(slide, index, dark=False, left_text="Most Valuable Parent"):
    c = MUTED if not dark else RGBColor(0x7A, 0x70, 0x62)
    tf = textbox(slide, MARGIN, FOOTER_Y, 6000000, 338138)
    write(tf, left_text, MONO, SZ_MONO, c)
    tf = textbox(slide, W - MARGIN - 2000000, FOOTER_Y, 2000000, 338138)
    write(tf, f"{index:02d} / {TOTAL_SLIDES}", MONO, SZ_MONO, c, align=PP_ALIGN.RIGHT)


def notes(slide, text):
    slide.notes_slide.notes_text_frame.text = text


def picture(slide, name, x, y, height):
    path = ASSETS / name
    pic = slide.shapes.add_picture(str(path), Emu(x), Emu(y), height=Emu(height))
    return pic


# ------------------------------------------------------------------ deck
def build():
    prs = Presentation()
    prs.slide_width, prs.slide_height = Emu(W), Emu(H)
    n = 0

    # ---- 01 title -------------------------------------------------------
    n += 1
    s = new_slide(prs)
    rect(s, MARGIN, 2200000, 533400, 38100, TEAL_ALT)
    tf = textbox(s, MARGIN, 1700000, 8000000, 338138)
    write(tf, "MVP · MOST VALUABLE PARENT", MONO, SZ_MONO, TEAL)
    title(s, "Nobody should have to be\nthe only one who remembers.",
          size=76, y=2900000, w=int(CONTENT_W * 0.86))
    paragraph(s,
              "MVP finds the camps, watches the registration windows, and turns the "
              "school's PDF into both homes' calendars. It works even when only one "
              "parent uses it.",
              y=6250000, w=int(CONTENT_W * 0.62), size=24)
    tf = textbox(s, MARGIN, FOOTER_Y, 9000000, 338138)
    write(tf, "Pre-seed · 2026 · Heather Hannan-Kramer · Miguel Alvarado",
          MONO, SZ_MONO, MUTED)
    notes(s, "One sentence they can repeat to their partner. Say it and move on.")

    # ---- 02 thesis (dark) -----------------------------------------------
    n += 1
    s = new_slide(prs, dark=True)
    eyebrow(s, "The thesis", dark=True)
    title(s, "Agentic software escaped the enterprise.", size=66, dark=True,
          w=int(CONTENT_W * 0.92))
    paragraph(s,
              "Two years ago, AI that could actually do things arrived for engineers. "
              "It holds the whole context, makes a plan, takes the next step, and can be "
              "trusted with the result. Claude Code turned one engineer into a team. "
              "That capability is general now. It has not reached the household.",
              y=3150000, w=int(CONTENT_W * 0.80), dark=True)
    cards(s, [
        ("What engineers got",
         "An agent that holds the context, works while they sleep, and hands back "
         "finished work."),
        ("What parents got",
         "A chatbot that has never heard of their kids."),
        ("What we built",
         "The first one, pointed at the second job."),
    ], y=5500000, h=2400000, dark=True)
    footer(s, n, dark=True)
    notes(s, "This is the whole company in one line. Say it and stop talking.")

    # ---- 03 problem ------------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "The problem")
    title(s, "The last unmanaged operations job in America.", w=int(CONTENT_W * 0.9))
    paragraph(s, "Sales got Salesforce. Engineering got Claude Code. The family got a "
                 "group text.", y=2620000)
    stat_cards(s, [
        ("85%", "of parents lose sleep over summer care and scheduling. 90% among "
                "working parents.", "Bright Horizons Modern Family Index · Harris Poll · Apr 2026"),
        ("80+", "school and activity emails a month.",
         "Yahoo / Censuswide · Jun 2024"),
        ("62%", "have already missed something buried in one.",
         "Yahoo / Censuswide · Jun 2024"),
    ], y=4000000, h=4200000)
    footer(s, n)
    notes(s, "Three numbers, no argument. Every parent is doing the math on their own inbox.")

    # ---- 04 why now ------------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "Why now")
    title(s, "Milo was right in 2024.\nThey are wrong in 2026.", w=int(CONTENT_W * 0.8))
    quote_y = 3900000
    rect(s, MARGIN, quote_y, CONTENT_W, 1500000, CARD, MSO_SHAPE.ROUNDED_RECTANGLE, RADIUS)
    tf = textbox(s, MARGIN + CARD_PAD_X, quote_y + 300000,
                 CONTENT_W - 2 * CARD_PAD_X, 1000000)
    write(tf, "“the technology is simply too early to be reliable in any useful way”",
          DISPLAY, 32, INK, italic=True, spacing=1.2)
    write(tf, "Milo, shutting down, 12 January 2026", MONO, 15, MUTED,
          space_after=0, first=False)
    cards(s, [
        ("Agents crossed the reliability line",
         "Tool calling plus real eval infrastructure is the difference between a demo "
         "and a deadline. That gap closed in the last eighteen months."),
        ("Voice went conversational",
         "Sub-150ms round trip. A parent in the carpool line can talk to it now."),
        ("The category cleared",
         "Milo closed January 2026. Yohana left the US in September 2025. Meanwhile "
         "TalkingParents killed its free plan and AppClose went paid, so demand is "
         "inelastic enough to raise prices into."),
    ], y=5750000, h=2600000)
    footer(s, n)
    notes(s, "A competitor's own words are the timing argument. The third card answers "
             "the skeptic who reads the same fact as 'this category kills companies'.")

    # ---- 05 the moment ---------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "The job")
    title(s, "It's 11pm and she just remembered the deadline.", w=int(CONTENT_W * 0.92))
    paragraph(s, "That is the moment we build for. She does not need advice, a course, "
                 "or a chatbot. She needs someone to have already handled it.",
              y=2620000, w=int(CONTENT_W * 0.72))
    r = cards(s, [
        ("She photographs the flyer",
         "The agent pulls out every date, fee and deadline in it."),
        ("It checks the whole family",
         "Ages, conflicts, the other kid's Tuesdays, what she said about last summer."),
        ("It watches what she can't",
         "The registration window that opens in nine days at 9am."),
    ], y=4150000, h=2500000)
    tf = textbox(s, MARGIN, r + 340000, CONTENT_W, 700000)
    write(tf, "One agent, one memory, five doors in:  camps · classes & sports · "
              "school life · outings · trips", TEXT, 21, INK, bold=True, spacing=1.3)
    footer(s, n)
    notes(s, "Lead with the moment, reveal the system second.")

    # ---- 06 wedge --------------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "The wedge")
    title(s, "The window opens at 9am\non a Tuesday in February.", w=int(CONTENT_W * 0.8))
    paragraph(s, "Miss it and the camp is full, the summer has a hole in it, and the "
                 "other parent finds out before you do. No national product watches "
                 "these dates for parents.", y=3550000, w=int(CONTENT_W * 0.72))
    cards(s, [
        ("We watch the window",
         "Seven days out, and again before it opens. Never after."),
        ("We confirm, we don't guess",
         "A date the agent researched stays labelled an estimate until the parent taps "
         "to confirm it."),
        ("An alarm watches the watcher",
         "A miss detector pages us when a window closes unnotified. We do not expand "
         "past the pilot metros until it runs clean through a real season."),
    ], y=5300000, h=2900000)
    footer(s, n)
    notes(s, "This is the retention engine. Not the coaching.")

    # ---- 07 evidence -----------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "The evidence")
    title(s, "It shows you the sentence it got the date from.", w=int(CONTENT_W * 0.94))
    paragraph(s, "It puts the source sentence right beside the deadline, so a parent "
                 "can see it invented nothing. That detail only exists when someone "
                 "builds for five months instead of demoing for five weeks.",
              y=2560000, w=int(CONTENT_W * 0.86))
    row = [
        ("Live on TestFlight",
         "Onboarding, companions, and coaching grounded in a real family profile."),
        ("Backend in production",
         "24 schema migrations, 4 live alert rules, per-call cost telemetry."),
        ("Five-layer moderation",
         "Crisis detection on a taxonomy aligned to 988 / SAMHSA vocabulary."),
    ]
    row2 = [
        ("Tested like infrastructure",
         "567 automated tests. 120 kid-safety evals. 29 flow specs driven against "
         "the real API."),
        ("Voice, sub-150ms",
         "Our backend stays the brain. The vendor only moves audio."),
        ("Content taxonomy",
         "110 categories, 45 articles, 25 community posts mapped."),
    ]
    r = cards(s, row, y=4300000, h=2050000)
    cards(s, row2, y=r + 200000, h=2050000)
    footer(s, n)
    notes(s, "Heather's credibility slide, hardened. The headline is the detail, not the count.")

    # ---- 08 scale case ---------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "The scale case")
    title(s, "Camps is the wedge. The household is the company.",
          w=int(CONTENT_W * 0.94))
    paragraph(s, "A seasonal tool is a good business. This gets big because solving one "
                 "deadline earns the right to the rest of the household, and the graph "
                 "we build getting there cannot be bought.",
              y=2560000, w=int(CONTENT_W * 0.88))
    r = cards(s, [
        ("Act one · the wedge",
         "Activities and coverage. One acute, recurring, seasonally forced pain."),
        ("Act two · the household",
         "The agent already reads the email, the calendar and the paperwork. Medical "
         "and school logistics are adjacent, not new."),
    ], y=4200000, h=2000000, n=2)
    cards(s, [
        ("Act three · the transaction",
         "We source registrations that today flow through nobody who knows the family. "
         "$3-4B a year in US camp fees alone."),
        ("Why not OpenAI",
         "They will not take on child-safety liability, they do not have your family's "
         "graph, and trust here is won by a product a parent hands their kid, not by a "
         "better model."),
    ], y=r + 200000, h=2100000, n=2)
    footer(s, n)
    notes(s, "If they think this is a lifestyle business, it is because we did not say this.")

    # ---- 09 moat ---------------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "The moat")
    title(s, "What compounds.")
    paragraph(s, "The honest question at pre-seed is not what our moat is today. It is "
                 "what we are accumulating.", y=2560000, w=int(CONTENT_W * 0.7))
    r = cards(s, [
        ("The family graph",
         "Ages, interests, custody rhythm, what you tried last year and what you said "
         "about it. Every conversation deepens it. A general assistant starts from zero "
         "every session, forever."),
        ("Safety as architecture",
         "Five layers, and a crisis lock that freezes the conversation and pushes the "
         "parent's phone, verified on a physical device. Months of work, and the part a "
         "fast follower skips."),
    ], y=3900000, h=2250000, n=2)
    cards(s, [
        ("Evals that keep it honest",
         "Every change to a prompt or a tool re-runs a live-model golden set before it "
         "ships. It is why the agent still works in month eight."),
        ("Solo-first coordination",
         "A co-parenting app only learns how a family runs once both parents sign up. "
         "We learn it from one side, then confirm it through the invites the other "
         "parent accepts. Our graph grows at one account per family. Theirs needs two, "
         "and the second is the one that says no."),
    ], y=r + 200000, h=2350000, n=2)
    footer(s, n)
    notes(s, "If they underwrite one slide, it is this one.")

    # ---- 10 safety -------------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "Safety")
    title(s, "If a child is in crisis, a parent's phone rings.", w=int(CONTENT_W * 0.94))
    paragraph(s, "Safety here is architecture, not a content filter bolted onto a "
                 "chatbot. Five layers sit between a child and a wrong answer, and when "
                 "it matters the system stops talking and gets a human involved.",
              y=2560000, w=int(CONTENT_W * 0.88))
    r = cards(s, [
        ("Five layers",
         "Deterministic patterns, a moderation API, an age classifier, a streaming "
         "token-level monitor, and a final output check. The model sits on top of the "
         "backstop, never underneath it."),
        ("A real taxonomy",
         "Severity aligned to 988 / SAMHSA ideation vocabulary and reviewed against "
         "pediatric safety practice."),
    ], y=4200000, h=2100000, n=2)
    cards(s, [
        ("The parent is paged",
         "A crisis freezes the conversation, shows the child real resources, and pushes "
         "the parent's phone. Verified on device, July 2026."),
        ("Privacy as a position",
         "Logistics data is durable and exportable. The coaching conversation is "
         "designed to leave nothing behind."),
    ], y=r + 200000, h=2100000, n=2)
    footer(s, n)
    notes(s, "Heather leads this one. It is the trust slide, and the reason a "
             "parent hands us their kid at all.")

    # ---- 11 market -------------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "The market")
    title(s, "Parents already pay. Twice, and for less.", w=int(CONTENT_W * 0.9))
    paragraph(s, "We are not sizing a circle. We are pointing at cash registers already "
                 "ringing next door.", y=2560000, w=int(CONTENT_W * 0.7))
    r = stat_cards(s, [
        ("$34M", "Good Inside's 2025 revenue. 100,000+ subscribers at roughly $276 a "
                 "year, for parenting advice with no coordination and no deadlines.",
         "Fortune · Feb 2026"),
        ("$110-300", "OurFamilyWizard's annual price, charged per parent. Two-household "
                     "families already pay twice, for software built to be read by a judge.",
         "OurFamilyWizard pricing page"),
        ("$3-4B", "US summer camp registrations a year, intermediated today by nobody "
                  "who knows the family.", "Category estimate"),
    ], y=3900000, h=3600000)
    tf = textbox(s, MARGIN, r + 200000, int(CONTENT_W * 0.92), 750000)
    write(tf, "100,000 families at $129 a year is $12.9M of ARR. Good Inside reached "
              "that subscriber count selling advice alone. We price at about 3% of what "
              "the activities themselves cost, one payer, hard paywall after a trial.",
          TEXT, 20, INK, spacing=1.3)
    footer(s, n)
    notes(s, "Bottoms-up from three verified anchors. If they push on TAM, push back with these.")

    # ---- 12 why we win ---------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "Why we win")
    title(s, "Every other app needs\nyour ex to sign up.", size=72, y=2900000,
          w=int(CONTENT_W * 0.82))
    paragraph(s, "TalkingParents publishes a help article called “What if my "
                 "co-parent won't sign up?” The industry's answer is a contempt "
                 "motion. Ours is a calendar invite.",
              y=6100000, w=int(CONTENT_W * 0.62), size=24)
    tf = textbox(s, MARGIN, 8000000, int(CONTENT_W * 0.8), 600000)
    write(tf, "They document the fight. We prevent it. ChatGPT is better than us at "
              "nearly everything and has never heard of your custody schedule.",
          TEXT, 19, MUTED, spacing=1.3)
    footer(s, n)
    notes(s, "Let the title sit on a white field. Do not fill the slide.")

    # ---- 13 where we are -------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "Where we are")
    title(s, "Five months. In stealth. On purpose.", w=int(CONTENT_W * 0.9))
    paragraph(s, "We have not launched. We spent the time on what kills consumer AI "
                 "companies: reliability, safety, and the evals that keep both true "
                 "after the demo.", y=2560000, w=int(CONTENT_W * 0.74))
    cards(s, [
        ("What is built",
         "Five verticals live in production. A 20-tool agent. 98 TestFlight builds. "
         "21 parent-facing releases in the last 24 days."),
        ("What is not",
         "No public launch. No revenue. No paywall in the app yet. We are not dressing "
         "a beta up as traction."),
        ("How we will know",
         "The gates are written down in advance, with the numbers that would make us "
         "stop: median willingness to pay at or above $100, cost per email at or under "
         "$5, and 90-day retention above 30% before we scale spend."),
    ], y=4300000, h=3400000)
    footer(s, n)
    notes(s, "Say it out loud: we wrote down what would make us quit.")

    # ---- 14 team ---------------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "The team")
    title(s, "Both of our beachhead customers\nare sitting at the table.",
          w=int(CONTENT_W * 0.86))
    paragraph(s, "Founder-market fit here is structural. Two founders, two different "
                 "household structures, overlapping kid ages. The product's two "
                 "personas are the two people building it.",
              y=3550000, w=int(CONTENT_W * 0.74))
    cards(s, [
        ("Heather Hannan-Kramer · CEO",
         "Parent, educator, consultant. Originated the concept before the pandemic. "
         "Owns product vision, audience research and go-to-market. The coordinating "
         "mother the product is designed for, with two girls at home."),
        ("Miguel Alvarado · CTO",
         "Single father of two. Thirty years shipping software, thirteen in AI, twice a "
         "CTO. Built the whole stack: the native Swift app, the agent backend, the\n"
         "moderation system, the deploy."),
        ("Greg Harris · Design",
         "Grandparent, and a design leader on consumer products. Owns visual identity "
         "and the user journey from prototype to market."),
    ], y=5300000, h=2900000)
    footer(s, n)
    notes(s, "VCs weight team about 40% more than they used to. AI made building easy, "
             "so who builds matters more.")

    # ---- 15 CTO ----------------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "The technical co-founder")
    title(s, "Thirty years of range, in the year\nrange became the qualification.",
          w=int(CONTENT_W * 0.88))
    paragraph(s, "Breadth used to be a liability. AI inverted that: when one engineer "
                 "holds the backend, the app, the model layer and the deploy in one "
                 "head, the person who has worked at every layer is the one who ships.",
              y=3400000, w=int(CONTENT_W * 0.92))
    cards(s, [
        ("30 years shipping",
         "Microsoft in the Web 1.0 era. Brightcove through IPO, 450M players and "
         "~1.3B daily video views. Intel Media's OnCue through the Verizon "
         "acquisition. VP Engineering at Vevo."),
        ("13 years in AI",
         "CTO at Lumiata, deep learning across 100+ medical conditions. CTO at "
         "Mindstrong, digital biomarkers, reliability from 92% to 99.99%, acquired by "
         "SonderMind. VP Engineering at SonderMind today."),
        ("AI-first, and board-facing",
         "Multi-agent systems, real-time voice and regulated guardrails, built "
         "hands-on through Artesano. Board-facing at Lumiata and MetaStories. Ten "
         "years advising Loupe, with a three-part patent."),
    ], y=5000000, h=2000000)
    band_y = getattr(s, "_row_bottom", 0) + 170000
    rect(s, MARGIN, band_y, CONTENT_W, 1000000, CARD,
         MSO_SHAPE.ROUNDED_RECTANGLE, RADIUS)
    tf = textbox(s, MARGIN + CARD_PAD_X, band_y + 200000,
                 CONTENT_W - 2 * CARD_PAD_X, 720000)
    write(tf, "The proof is not the résumé. It is this product: one engineer, five "
              "months. A native Swift app, a Python agent backend, a React dashboard. "
              "~77,000 lines. 567 tests. 120 kid-safety evals. 98 builds.",
          TEXT, 20, INK, bold=True, spacing=1.3)
    footer(s, n)
    notes(s, "The last card is the point. Do not read the résumé, read the last card.")

    # ---- 15b CTO, short version -----------------------------------------
    # Two candidates for slide 15. Keep one, delete the other before sending.
    s = new_slide(prs)
    eyebrow(s, "The technical co-founder")
    title(s, "Thirty years shipping.\nThirteen in AI. Twice a CTO.",
          size=62, w=int(CONTENT_W * 0.86))
    paragraph(s, "Miguel Alvarado. I built every layer of MVP myself, in five months.",
              y=4300000, w=int(CONTENT_W * 0.8), size=24)
    cards(s, [
        ("Shipped at scale",
         "Microsoft. Brightcove through IPO. Intel Media into Verizon. VP Engineering "
         "at Vevo."),
        ("AI in production",
         "CTO at Lumiata and at Mindstrong, acquired by SonderMind. VP Engineering at "
         "SonderMind today."),
        ("Building MVP",
         "Native Swift app, agent backend, five-layer safety system. One engineer."),
    ], y=6000000, h=2200000)
    footer(s, n)
    notes(s, "ALTERNATIVE to the previous slide. Pick one and delete the other. "
             "Use this one if the deck is already running long.")

    # ---- 16 the ask ------------------------------------------------------
    n += 1
    s = new_slide(prs)
    eyebrow(s, "The ask")
    title(s, "Fund the proof, not the promise.")
    paragraph(s, "The product risk is behind us. What we are buying is the answer to one "
                 "question: will parents pay for this, at this price, without us in the "
                 "room.", y=2560000, w=int(CONTENT_W * 0.72))
    cards(s, [
        ("Prove they will pay",
         "Run the gates in the pilot metros. The numbers that matter are median "
         "willingness to pay at or above $100 and 90-day retention above 30%."),
        ("Survive one season",
         "The miss detector runs clean through a real winter-into-spring registration "
         "cycle. That is the difference between a product and a promise."),
        ("Close the two known gaps",
         "COPPA compliance, which unlocks the kid companion we are sitting on, and the "
         "move off a single-writer database before scale demands it."),
    ], y=4200000, h=2900000)
    tf = textbox(s, MARGIN, 7600000, int(CONTENT_W * 0.86), 1200000)
    write(tf, "Every hard coordination job in the economy got software. The family is "
              "the last one holding out, and the technology that finally solves it "
              "arrived eighteen months ago. We built the thing. We would like to go "
              "find out what it is worth.", DISPLAY, 24, INK, italic=True, spacing=1.3)
    footer(s, n)
    notes(s, "End on the closing line. No thank-you slide.")

    audit(prs)
    prs.save(str(OUT))
    print(f"wrote {OUT}")


def audit(prs):
    """Flag any content that runs into the footer band or off the canvas.

    Text heights are estimates, so this is the safety net: it turns a layout
    bug into a printed line instead of something you have to spot by eye.
    """
    limit = FOOTER_Y - 120000
    problems = 0
    for i, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if shape.width == W and shape.height == H:
                continue                       # background
            bottom, right = shape.top + shape.height, shape.left + shape.width
            label = (shape.text_frame.text[:38].replace("\n", " ")
                     if shape.has_text_frame else "<picture>")
            if shape.top == FOOTER_Y:
                continue                       # the footer text itself
            if bottom > limit:
                print(f"  ! slide {i:02d} overflows footer by "
                      f"{(bottom - limit) / 914400:.2f}in: {label!r}")
                problems += 1
            if right > W - MARGIN + 20000:
                print(f"  ! slide {i:02d} overflows right margin: {label!r}")
                problems += 1
    print(f"audit: {problems} layout problem(s)")


if __name__ == "__main__":
    build()
