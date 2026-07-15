"""
Generate the MVP Ground Zero document as a formatted .docx
with the Hearth design system's color palette and voice.
"""
from docx import Document
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import os

# Hearth palette
CREAM = RGBColor(0xF3, 0xF0, 0xEB)
INK_PRIMARY = RGBColor(0x1A, 0x1A, 0x1A)
INK_SECONDARY = RGBColor(0x2D, 0x2D, 0x2D)
INK_MUTED = RGBColor(0x6F, 0x6A, 0x60)
OLIVE = RGBColor(0x4F, 0x5D, 0x3A)
OLIVE_DARK = RGBColor(0x3A, 0x4A, 0x2A)
OLIVE_TINT = RGBColor(0xE8, 0xEB, 0xDC)
SAFFRON = RGBColor(0xE8, 0xA3, 0x3C)
ROSE = RGBColor(0xB8, 0x6A, 0x60)
ROYAL = RGBColor(0x2E, 0x3A, 0x5F)
FOREST = RGBColor(0x2D, 0x3F, 0x2C)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def set_cell_bg(cell, color_hex):
    """Set background color of a table cell."""
    shading = OxmlElement('w:shd')
    shading.set(qn('w:fill'), color_hex)
    shading.set(qn('w:val'), 'clear')
    cell._tc.get_or_add_tcPr().append(shading)


def add_horizontal_rule(doc):
    """Add a subtle horizontal rule."""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(12)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '4')
    bottom.set(qn('w:space'), '1')
    bottom.set(qn('w:color'), '6F6A60')
    pBdr.append(bottom)
    pPr.append(pBdr)


def create_doc():
    doc = Document()

    # Page margins
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(3)
        section.right_margin = Cm(3)

    # Style: Normal
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Georgia'
    font.size = Pt(11)
    font.color.rgb = INK_PRIMARY
    style.paragraph_format.line_spacing = 1.4
    style.paragraph_format.space_after = Pt(6)

    # Style: Heading 1
    h1 = doc.styles['Heading 1']
    h1.font.name = 'Georgia'
    h1.font.size = Pt(28)
    h1.font.bold = True
    h1.font.color.rgb = INK_PRIMARY
    h1.paragraph_format.space_before = Pt(36)
    h1.paragraph_format.space_after = Pt(12)

    # Style: Heading 2
    h2 = doc.styles['Heading 2']
    h2.font.name = 'Georgia'
    h2.font.size = Pt(18)
    h2.font.bold = True
    h2.font.color.rgb = OLIVE_DARK
    h2.paragraph_format.space_before = Pt(24)
    h2.paragraph_format.space_after = Pt(8)

    # Style: Heading 3
    h3 = doc.styles['Heading 3']
    h3.font.name = 'Georgia'
    h3.font.size = Pt(14)
    h3.font.bold = True
    h3.font.color.rgb = INK_SECONDARY
    h3.paragraph_format.space_before = Pt(18)
    h3.paragraph_format.space_after = Pt(6)

    # === COVER ===
    for _ in range(3):
        doc.add_paragraph()

    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run('MVP')
    run.font.name = 'Georgia'
    run.font.size = Pt(48)
    run.font.bold = True
    run.font.color.rgb = OLIVE_DARK

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run('Most Valuable Parent')
    run.font.name = 'Georgia'
    run.font.size = Pt(20)
    run.font.color.rgb = INK_SECONDARY

    doc.add_paragraph()

    tagline = doc.add_paragraph()
    tagline.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = tagline.add_run('Ground Zero Document')
    run.font.name = 'Georgia'
    run.font.size = Pt(14)
    run.font.color.rgb = INK_MUTED

    doc.add_paragraph()
    doc.add_paragraph()

    meta = doc.add_paragraph()
    meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = meta.add_run('June 2026 · revised July 12, 2026\nMiguel Alvarado, Heather Hannan-Kramer, Greg Harris')
    run.font.name = 'Georgia'
    run.font.size = Pt(11)
    run.font.color.rgb = INK_MUTED

    doc.add_page_break()

    # === TABLE OF CONTENTS (simple) ===
    doc.add_heading('Contents', level=1)
    toc_items = [
        '1. The Problem We Solve',
        '2. Who We Serve',
        '3. What MVP Is',
        '4. Who We Are',
        '5. What We Have Built So Far',
        '6. How It Looks and Feels',
        '7. How Content Is Organized',
        '8. What Is Next',
        '9. Beta Launch Plan',
        '10. Decisions from Our First Meeting',
        '11. Market Opportunity',
        '12. Go-To-Market Strategy',
    ]
    for item in toc_items:
        p = doc.add_paragraph(item)
        p.paragraph_format.space_after = Pt(4)
        p.runs[0].font.color.rgb = OLIVE

    doc.add_page_break()

    # === SECTION 1: THE PROBLEM ===
    doc.add_heading('1. The Problem We Solve', level=1)

    doc.add_paragraph(
        'Modern parents face two compounding crises, and no product solves both.'
    )

    doc.add_heading('The emotional crisis: isolation', level=3)
    doc.add_paragraph(
        'The village that used to raise children has dissolved into a scroll of '
        'conflicting advice, algorithmic feeds designed to maximize anxiety, and clinical '
        'apps that make you feel like a patient instead of a person. Parents don\'t need '
        'more content. They need a steady hand on the shoulder—a friend who knows your '
        'kid\'s name, remembers what you said last Tuesday, and gives you one clear thing '
        'to try tonight.'
    )

    doc.add_heading('The operational crisis: invisible labor', level=3)
    doc.add_paragraph(
        'Every parent is also an unpaid project manager. Camp registrations close silently. '
        'Permission slips hide in email threads. Practice schedules arrive via group text '
        'and are forgotten by dinner. Multiply by two or three kids and the cognitive load '
        'becomes unsustainable. Studies show 59% of dual-income mothers manage their '
        'children\'s schedules solo even when both parents work full-time. It\'s not that '
        'parents are disorganized—it\'s that the information arrives scattered across too '
        'many channels with no system to catch it.'
    )

    doc.add_heading('Why both matter', level=3)
    doc.add_paragraph(
        'The parenting space today is dominated by two extremes: clinical tools that feel '
        'like hospital intake forms (Bumo/Benny), and entertainment feeds that waste the '
        'precious 3 minutes a parent has. Neither solves both problems. We do. The emotional '
        'companion and the operational manager share the same living family profile—so the '
        'agent that reminds you about camp registration also knows your kid just started '
        'a new medication and might need a lower-key week.'
    )

    doc.add_heading('The opportunity', level=3)
    doc.add_paragraph(
        'Agentic AI has succeeded in enterprise (coding assistants, research copilots). '
        'It has not yet been applied thoughtfully to the consumer space—specifically to '
        'parents. The technology is ready. The market is underserved. The timing is now.'
    )

    add_horizontal_rule(doc)

    # === SECTION 2: WHO WE SERVE ===
    doc.add_heading('2. Who We Serve', level=1)

    doc.add_paragraph(
        'MVP is built for every kind of family. Not the "soccer mom" stereotype. Not the '
        'two-parent, two-kid, suburban household that most parenting apps quietly assume. '
        'The reality of modern families is vastly more diverse—and our product is '
        'architected from day one to reflect that reality.'
    )

    doc.add_heading('Our families include', level=3)
    family_types = [
        'Single moms navigating everything alone.',
        'Single dads—often invisible in the parenting product space.',
        'Same-sex couples (two moms, two dads) building their families.',
        'Gay and lesbian single parents.',
        'Blended families with step-parents and half-siblings.',
        'Co-parenting households (divorced, never-married) coordinating across two homes.',
        'Grandparents raising grandchildren (2.4 million in the US alone).',
        'Foster and adoptive parents—often managing complex needs with less support.',
        'Military families relocating every 2-3 years, rebuilding community each time.',
        'Multi-generational households where aunts, uncles, and grandparents co-parent.',
        'Non-binary and trans parents whose families don\'t fit binary forms.',
    ]
    for ft in family_types:
        p = doc.add_paragraph(ft, style='List Bullet')
        p.runs[0].font.size = Pt(11)

    doc.add_heading('How the product reflects this', level=3)
    doc.add_paragraph(
        'From the moment you open MVP, the app asks who is in your family—not which slot '
        'they fill. There is no "mom" box and "dad" box. You tell it who the caregivers are, '
        'how many kids, their ages, your situation. The app remembers all of it and uses it '
        'to personalize everything: the advice it gives, the content it surfaces, the events '
        'it suggests. A single dad with three kids gets the same depth of support as a '
        'two-parent household. A grandmother raising her grandchild sees information relevant '
        'to her reality, not "first trimester nausea tips." The system adapts to the family '
        'in front of it—it never assumes a shape.'
    )
    doc.add_paragraph(
        'This isn\'t a feature we bolt on later. It\'s a foundational design decision. '
        'Every screen, every recommendation, every piece of content is built to work for '
        'the full spectrum of families from day one—because that\'s who parents actually are.'
    )

    add_horizontal_rule(doc)

    # === SECTION 3: WHAT MVP IS ===
    doc.add_heading('3. What MVP Is', level=1)

    doc.add_paragraph(
        'MVP (Most Valuable Parent) is a family companion app. It is not a content feed. '
        'It is not a scheduling tool. It is not a clinical intervention. It is the wise, '
        'warm friend you wish you had—powered by AI that actually knows your family.'
    )

    doc.add_heading('For the parent', level=3)
    bullets = [
        'A coaching agent that knows your family profile, your kids\' ages and temperaments, '
        'your parenting philosophy, and your current challenges.',
        'Curated editorial content—not a fire hose. Articles written in the voice of '
        'trusted experts (Becky Kennedy, Andrew Huberman, Daniel Amen, Gabor Maté) '
        'but adapted to your family\'s specific situation.',
        'A community of real parents—not influencers—sharing what actually works.',
    ]
    for b in bullets:
        p = doc.add_paragraph(b, style='List Bullet')
        p.runs[0].font.size = Pt(11)

    doc.add_heading('For the child', level=3)
    bullets = [
        'A kid companion—an age-appropriate AI friend that the parent configures, '
        'monitors, and can shut down at any time.',
        'Voice-first interaction. The child speaks; the companion speaks back. Natural, '
        'low-latency, real-time conversation.',
        'Five layers of safety moderation. Crisis detection (self-harm, abuse, suicide) '
        'triggers immediate parent notification, conversation freeze, and crisis resources.',
        'The parent sees every transcript. Non-negotiable.',
    ]
    for b in bullets:
        p = doc.add_paragraph(b, style='List Bullet')
        p.runs[0].font.size = Pt(11)

    doc.add_heading('For the family\'s schedule', level=3)
    bullets = [
        'A parenting agenda manager—an AI agent that proactively finds camps, activities, '
        'events, and deadlines relevant to your kids based on their ages, interests, and location.',
        'Reads your email and text messages (with permission) to extract event details, '
        'registration deadlines, permission slips, and schedule changes that are already '
        'sitting in your inbox unread.',
        'Builds and maintains a family calendar—synced to Google Calendar—so you have one '
        'place to see what\'s coming for every kid.',
        'Manages reminders and to-dos: "Summer camp registration closes Friday." '
        '"Bring swim gear Monday." "Science fair materials due next week." The things that '
        'fall through the cracks when you\'re juggling multiple kids.',
    ]
    for b in bullets:
        p = doc.add_paragraph(b, style='List Bullet')
        p.runs[0].font.size = Pt(11)

    doc.add_heading('The handoff', level=3)
    doc.add_paragraph(
        'The parent sets up the child\'s companion on their device (phone or tablet), '
        'configures it via a "letter" that defines the companion\'s personality and boundaries, '
        'then hands the device to the child. The parent can take the device back at any time. '
        'This is not an unsupervised app for children—it is a supervised tool the parent '
        'deploys intentionally.'
    )

    add_horizontal_rule(doc)

    # === SECTION 4: WHO WE ARE ===
    doc.add_heading('4. Who We Are', level=1)

    people = [
        ('Heather Hannan-Kramer — CEO & Co-founder', [
            'Parent, educator, consultant. Originated the product concept pre-pandemic. '
            'Owns product vision, audience research, personas, go-to-market strategy, '
            'and investor relationships.',
            'The person who knows what parents actually need because she is one and '
            'has talked to hundreds.',
        ]),
        ('Miguel Alvarado — CTO & Technical Co-founder', [
            'Single father of two. Software engineer. Built the entire technical stack '
            'end-to-end: backend, iOS app, AI agent pipeline, moderation system, CMS, deployment.',
            'Runs the development and ships code.',
        ]),
        ('Greg Harris — Head of Design', [
            'Grandparent ("wise owl" perspective across parenting stages). Design leader '
            'with experience on consumer products (previously Happily). Joining to own '
            'design strategy, Figma artifacts, user journeys, and the visual identity as '
            'it evolves from engineering prototype to market-ready product.',
            'Brings the "form follows function" discipline and the question: '
            '"does this actually solve the problem, or does it just look good?"',
        ]),
    ]

    for name, descs in people:
        doc.add_heading(name, level=3)
        for d in descs:
            doc.add_paragraph(d)

    add_horizontal_rule(doc)

    # === SECTION 5: WHAT WE HAVE BUILT ===
    doc.add_heading('5. What We Have Built So Far', level=1)

    doc.add_paragraph(
        'This is not a pitch deck or a wireframe. We have a working product in active '
        'development. Here is what exists today, explained without jargon.'
    )

    doc.add_heading('The iOS app (live on TestFlight)', level=2)
    items = [
        ('Onboarding', 'A multi-step flow that learns about the parent and their children. '
         'Collects name, kid names/ages, parenting philosophy, challenges, location, '
         'cultural background. Two paths: structured form or conversational chat with the AI. '
         'Hardened after real beta-family incidents so a fresh install can never silently '
         'lose a family\'s answers.'),
        ('Parent coaching agent', 'An AI assistant that remembers your family, adapts to your '
         'parenting style, and gives concrete, actionable advice. Not generic—it knows '
         'your kid\'s age band, your co-parenting situation, your stressors. Works by text '
         'or real-time voice.'),
        ('Kid companion agents', 'One AI companion per child, automatically generated from '
         'the parent\'s profile. Age-appropriate personality. Voice-first interaction '
         '(the child speaks, the companion speaks back). Parent writes a "letter" that '
         'defines boundaries and personality.'),
        ('Content library', 'Editorial articles organized by topic. Community posts from '
         'other parents. Saved articles. Tag-based filtering.'),
        ('Handoff mode', 'Parent pins a kid companion, hands the device to the child. '
         'A curtain covers the parent UI. Child interacts only with their companion.'),
        ('The Plan tab', 'A fifth tab, chat-first: the home of the family chief of staff '
         '(detailed below)—Chat, Discover, Shortlist, and Calendar in one place, plus '
         '"add from a message or photo" ingestion and a "Plan something" menu of entry '
         'doors (camps, classes & sports, weekend outings, family trips).'),
        ('Settings & profile control', 'A full settings hub: edit everything the system '
         'knows about you and each kid, review the family-wide "what we\'ve learned" '
         'profile, add or delete a kid profile (with complete data cleanup), and connect '
         'or disconnect Google accounts.'),
        ('In-app debug reporting', 'One tap sends diagnostics to the team—how beta '
         'families report issues without leaving the app.'),
    ]
    for title, desc in items:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('The backend (deployed on Railway)', level=2)
    items = [
        ('AI agent pipeline', 'Powered by OpenAI\'s latest model (GPT-5.5). Each kid companion '
         'runs through a multi-stage pipeline: prompt synthesis (builds the system prompt from '
         'the parent\'s letter + kid profile), then streams responses through a real-time '
         'moderation pipeline.'),
        ('Five-layer moderation', '50+ crisis keyword patterns, OpenAI content moderation API, '
         'age-appropriateness classifier, streaming token-by-token moderator, and a final '
         'output check. If anything triggers, the conversation freezes immediately.'),
        ('Crisis detection', 'Self-harm, abuse, and suicide language triggers an instant '
         'parent notification, conversation lock, and crisis resources displayed to the child. '
         'The agent cannot be restarted until the parent explicitly intervenes.'),
        ('Voice pipeline (v2 — shipped)', 'Real-time voice via ElevenLabs Conversational AI, '
         'live for both kid companions and the parent coach. WebRTC audio—under 150ms latency '
         'from the child speaking to the companion responding. The child just talks; '
         'no typing required.'),
        ('Intelligent family profile', 'Every interaction—parent coaching session, kid conversation, '
         'onboarding answer—feeds back into a living profile of the family. The system learns '
         'parenting style, kid temperaments, recurring challenges, and communication patterns '
         'over time. This isn\'t a static form you fill out once; it\'s a profile that gets '
         'smarter with every conversation, so the advice gets more relevant the longer you use it.'),
        ('Content management system', 'A web-based editor for creating and organizing articles, '
         'categories, and community posts, plus admin controls for the background agents '
         '(email-sync and calendar-sync schedules, run history). Used internally.'),
    ]
    for title, desc in items:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('The family chief of staff (shipped since the June meeting)', level=2)
    doc.add_paragraph(
        'The "parenting agenda manager" that Section 8 of the June draft described as our '
        'next major feature is now built, deployed to production, and validated with real '
        'family data. It is the operational half of the product—and, per Section 12, the '
        'centerpiece of our go-to-market. What exists today:'
    )
    cos_items = [
        ('All five verticals, live (July 11)', 'The "one agent, five entry doors" '
         'architecture from Section 12 is no longer a plan—it is deployed. One chief of '
         'staff handles camps & school breaks, weekly classes & sports (with real '
         'recurring schedules: "Tuesdays 4:00 PM through Dec 15"), school life (picture '
         'day, permission slips, fees), weekend outings, and family trips (dates, both '
         'calendars, packing lists—never bookings). Each is a door into the same agent '
         'and a filter chip on the same board, exactly as the strategy demands.'),
        ('The registration-window watchlist, live', 'Design commitment #2 from the '
         'adversarial review is shipped: tell the assistant when a registration opens '
         '("rec soccer signup opens August 12") and the app watches it—a push '
         'notification seven days ahead and again before it opens, never after. Dates '
         'the agent researched itself are labeled as estimates and the parent confirms '
         'them with one tap; dates you give us are a promise we keep at 100%. Every '
         'watched window is visible on its card ("Registration opens Aug 12 · '
         'watching"), and a miss-detector alarm watches the watcher.'),
        ('Activity discovery agent', 'A background research agent that finds real camps and '
         'activities near you—filtered by radius and a free-form focus ("art camps only"), '
         'scored against each kid\'s age and interests, with a live progress feed while it '
         'searches. Asks for the top N but reviews a much larger pool behind the scenes.'),
        ('Chief-of-staff chat', 'A conversational agent with 20 working tools: it compares '
         'shortlisted options ("help me decide"—cost, age eligibility, schedule conflicts, '
         'coverage gaps across kids and weeks), tracks decisions with rationale, manages '
         'to-dos, watches registration windows, drafts emails to camp directors (never '
         'sends), looks up and saves activities you already registered for, and can kick '
         'off new discovery runs mid-conversation.'),
        ('School-mail and flyer ingestion', 'Paste a newsletter or snap a photo of a paper '
         'flyer; the vision pipeline extracts EVERY item in it (a single PTA newsletter '
         'can carry picture day, a fundraiser, and a permission slip), spawns the right '
         'kind of to-do for each (form to sign, fee to pay), and shows every extracted '
         'deadline next to the exact sentence it came from—so a parent can verify at a '
         'glance instead of trusting a black box.'),
        ('Gmail agent', 'With permission (Google OAuth, shipped end-to-end), a daily agent '
         'reads camp-related email for registered activities and turns it into calendar '
         'entries and tasks.'),
        ('Two-way Google Calendar sync', 'The family plan lives where parents already look. '
         'Pulls external events in; pushes plan entries out—including a trip\'s all-day '
         'entries for each kid, so a co-parent sees the dates without anyone sending a text.'),
        ('The Plan hub', 'A chat-first iOS tab—Chat, Discover, Shortlist, Calendar—plus a '
         'full parent web dashboard (login, discovery, week-by-kid calendar with cost and '
         'coverage callouts, to-dos, chat) served from the same backend.'),
        ('Public product docs', 'A "How MVP works" site (no login required) ships with the '
         'dashboard: thirteen illustrated pages—real product screenshots, not mockups—'
         'covering every vertical plus the parenting coach and the kids\' companions '
         '(consent, moderation, crisis lock, parent-visible transcripts, in plain '
         'language). This is the first brick of the trust kit Section 12 calls for, and '
         'the page the validation funnel can link to.'),
        ('Profile editing everywhere', 'Parents can view and edit everything the system '
         'knows—about themselves, each kid, and the family-wide "what we\'ve learned" '
         'profile—on iOS and web, including adding and deleting kid profiles with full '
         'data cleanup.'),
        ('Production hardening', 'Error tracking (Sentry), metrics dashboards with live '
         'alerting to Slack (Grafana—including a dedicated watchlist reliability panel), '
         'cost logging per AI call, concurrency fixes proven under fault injection, '
         'guardrail tests for the bug classes our beta families actually hit, and a '
         'live-model evaluation gate: every change to the agent\'s instructions must '
         'pass a 27-scenario tool-selection exam and a 12-flyer extraction exam before '
         'it ships.'),
    ]
    for title, desc in cos_items:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('What works end-to-end today', level=2)
    doc.add_paragraph(
        'A parent can onboard, set up a kid companion, write a letter defining boundaries, '
        'hand the phone to their child, and the child can have a voice conversation with '
        'their AI companion—all moderated in real time, with transcripts visible to the parent. '
        'This is not a mockup. It runs.'
    )
    doc.add_paragraph(
        'And on the logistics side: a parent can ask for summer camps near them, watch real '
        'options stream in scored to each kid\'s age, save a shortlist, ask the chief of staff '
        'to compare them, snap a photo of a flyer from the school backpack, and see all of it '
        'land on a calendar that syncs with Google—live in production today.'
    )
    doc.add_paragraph(
        'As of July 11, the same is true across the whole activity year: "Mar is doing '
        'soccer this fall, every Tuesday at 4"—tracked with its real weekly schedule. '
        '"Rec soccer signup opens August 12"—watched, with reminders before it opens. '
        '"Picture day is October 9"—on the radar with the form and fee to-dos. "We\'re at '
        'grandma\'s August 14 to 18"—on both calendars, packing list started, and those '
        'days never show up as a childcare gap. One agent, five doors, one board.'
    )
    doc.add_paragraph(
        'None of this is demo-ware: real beta families use the production system today, and '
        'their bug reports have already driven hardening rounds (data-durability fixes, '
        'profile-edit cleanups, guardrail tests) that made the product sturdier than any '
        'internal testing could.'
    )

    add_horizontal_rule(doc)

    # === SECTION 6: HOW IT LOOKS AND FEELS ===
    doc.add_heading('6. How It Looks and Feels', level=1)

    doc.add_paragraph(
        'We have a complete design system called "Hearth." The name is the brief: '
        'warm, central, communal, slow. A hearth is where families gather.'
    )

    doc.add_heading('The six principles', level=2)
    principles = [
        ('Held', 'Every screen feels like a steady hand on the shoulder of an overwhelmed parent. '
         'Generous whitespace. One clear next action. No competing buttons demanding attention.'),
        ('Editorial', 'Content first, chrome quiet. Tiles are little magazine spreads, not widgets. '
         'Photography earns its space. The app feels like opening a beautiful magazine, not a '
         'hospital portal.'),
        ('Adaptive', 'Accessibility is non-negotiable. Large touch targets. Respects reduced-motion '
         'settings. Designed for cognitive accessibility—tired parents have less working memory.'),
        ('Real', 'No stock illustrations. No chirpy mascots. Photography shows actual parents '
         'in actual kitchens and yards. Side-lit, warm, golden. If a photo could appear in a '
         'competitor\'s ad, it doesn\'t belong here.'),
        ('Trustworthy', 'Safety surfaces (kid companion, crisis screens) go "sober"—quieter colors, '
         'no playful animation, no decorative elements. When a parent is scared, the app gets quieter.'),
        ('Hearth', 'Warmth without saccharin. Cream not white. Olive not mint. Ink not pure black. '
         'The gathering-place feeling.'),
    ]
    for name, desc in principles:
        p = doc.add_paragraph()
        run = p.add_run(name + '. ')
        run.bold = True
        run.font.color.rgb = OLIVE_DARK
        p.add_run(desc)

    doc.add_heading('The palette', level=2)
    doc.add_paragraph(
        'Cream canvas, ink text, olive accent. Photo tiles in four colors: saffron (energy/play), '
        'rose (care/tenderness), royal blue (focus/learning), and forest green (nature/outdoors). '
        'No neons. No gradients. No "tech blue."'
    )

    # Color swatches table
    table = doc.add_table(rows=5, cols=2)
    table.style = 'Table Grid'
    swatches = [
        ('Canvas (cream)', 'F3F0EB', INK_PRIMARY),
        ('Olive (accent)', '4F5D3A', WHITE),
        ('Saffron (energy)', 'E8A33C', INK_PRIMARY),
        ('Rose (care)', 'B86A60', WHITE),
        ('Forest (nature)', '2D3F2C', WHITE),
    ]
    for i, (name, hex_val, text_color) in enumerate(swatches):
        cell_name = table.cell(i, 0)
        cell_name.text = name
        cell_name.paragraphs[0].runs[0].font.size = Pt(10)

        cell_swatch = table.cell(i, 1)
        cell_swatch.text = f'  #{hex_val}  '
        set_cell_bg(cell_swatch, hex_val)
        cell_swatch.paragraphs[0].runs[0].font.color.rgb = text_color
        cell_swatch.paragraphs[0].runs[0].font.size = Pt(10)

    doc.add_paragraph()
    doc.add_heading('Typography', level=2)
    doc.add_paragraph(
        'Three fonts, each with a clear job. Fraunces (a warm serif) for display headlines—'
        'the ones that make you feel something. Inter (a clean sans-serif) for everything you '
        'read and tap. JetBrains Mono (a monospace font) for small metadata like dates and '
        'reading times. No fourth font. Ever.'
    )

    doc.add_heading('The voice', level=2)
    doc.add_paragraph(
        'Warm, concrete, second-person, present-tense. We write the way a friend with '
        'credentials would talk. Never a brand voice. Never a chatbot voice. Lowercase in '
        'buttons and navigation. Sentence case in body copy. Title Case only in article '
        'headlines. No emoji anywhere in the interface. Errors are warm and specific: '
        '"couldn\'t load articles. pull down to retry." Never "Error 500."'
    )

    add_horizontal_rule(doc)

    # === SECTION 7: HOW IT IS ORGANIZED ===
    doc.add_heading('7. How Content Is Organized', level=1)

    doc.add_paragraph(
        'We built a content taxonomy that covers the full parenting arc from pregnancy '
        'through teens. It uses three axes:'
    )

    doc.add_heading('11 parent categories (what the article is about)', level=3)
    categories = [
        'Pregnancy & Babies',
        'Raising Kids',
        'School & Activities',
        'Family Life & Relationships',
        'Health: Kids',
        'Health: Parents (Wellness)',
        'Food & Nutrition',
        'Care & Village',
        'Home, Style & Products',
        'Out in the World',
        'Inner Life',
    ]
    for i, cat in enumerate(categories, 1):
        p = doc.add_paragraph(f'{i}. {cat}')
        p.paragraph_format.space_after = Pt(2)

    doc.add_paragraph()
    doc.add_paragraph(
        'Each parent category contains 7–14 subcategories (99 total). For example, '
        '"Raising Kids" contains: Sleep, Behavior & Discipline, Emotional Intelligence, '
        'Communication, Milestones, Screen Time, Sibling Dynamics, Independence & Life Skills, '
        'and more.'
    )

    doc.add_heading('Tags (who it\'s for, what inspired it)', level=3)
    doc.add_paragraph(
        'Articles are tagged along several dimensions: age band (newborn through teen), '
        'parenting stage (first-time, single-parent, working-parent, postpartum), '
        'editorial voice (inspired-by-becky, inspired-by-huberman, etc.), and format '
        '(recipe, deep-dive, script, routine). Tags let us personalize what surfaces '
        'to each family without duplicating articles across categories.'
    )

    doc.add_heading('Status', level=3)
    doc.add_paragraph(
        'The taxonomy infrastructure is fully built: schema, API, CMS editor, iOS rendering. '
        '110 categories inserted (11 parents + 99 children). 45 articles and 25 community posts '
        'remapped to the new structure. Phase 2 (editorial pipeline with named-voice content) '
        'is next. Phase 3 (hierarchical browse UX on iOS) follows.'
    )

    add_horizontal_rule(doc)

    # === SECTION 8: WHAT IS NEXT ===
    doc.add_heading('8. What Is Next', level=1)

    doc.add_paragraph(
        'Prioritized by what moves us toward a beta-ready product by fall 2026.'
    )

    doc.add_heading('Must-ship for beta — status', level=2)
    must_ship = [
        ('Real user identity — SHIPPED', 'Native Apple and Google Sign-In with real '
         'accounts (rotating secure tokens) replaced the name-based login. Existing '
         'families were migrated without losing data. The "two Miguels collide" '
         'blocker is closed.'),
        ('Crisis parent notification — SHIPPED', 'A crisis in a kid companion now fires a '
         'real push notification to the parent\'s phone (verified on a physical device), '
         'locks the conversation, and stays locked until the parent reviews and '
         'reactivates.'),
        ('TestFlight release of the new experience — the one pending ship', 'The '
         'five-doors experience (all verticals, the watchlist, the illustrated docs) is '
         'live on the production backend and web dashboard; the iOS build that surfaces '
         'it (1.66) is built and verified and ships with the next TestFlight upload. '
         'Beta phones run the previous build until then—nothing breaks meanwhile.'),
        ('Onboarding polish — open', 'Low-friction, drip-style information collection. '
         'Don\'t ask for everything upfront. Let the app learn the family over time. '
         'Greg\'s WeTransfer insight: one simple action to start.'),
        ('Design review & dead ends — open', 'Greg will map the current user journeys in '
         'Figma, identify "dead ends" where the user gets stuck, and propose solutions.'),
    ]
    for title, desc in must_ship:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('The parenting agenda manager — shipped', level=2)
    doc.add_paragraph(
        'The June draft described this as our next major feature. It is now built and live '
        'in production—see "The family chief of staff" in Section 5. It became the '
        '"Superhuman for family scheduling" we sketched, and smarter than the sketch: '
        'it doesn\'t suggest teen coding camp for your 4-year-old, and it acts like the '
        'hyper-organized parent friend who texts you "hey, did you sign up for X yet?" '
        'What changed since June is the strategy around it: our market research (Section 12) '
        'concluded that this—not the coaching or the companions—is the front door of the '
        'business.'
    )

    doc.add_heading('The next unit of work is validation, not features', level=2)
    doc.add_paragraph(
        'The honest diagnosis from our July research: we have built a polished platform in '
        'silence, with zero waitlist and zero demand signal—the number-one founder mistake '
        'in every playbook we studied. The platform is over-built for a beta. Before '
        'greenlighting significant new feature work, we run the validation funnel described '
        'in Section 12 and let real market data pick our headline.'
    )

    doc.add_heading('Other important work (not blocking beta)', level=2)
    important = [
        ('Tablet support', 'iPad experience for the handoff—parents often give tablets '
         'to children, not phones. The architecture supports it; the UI needs adaptation.'),
        ('Editorial content pipeline', 'Systematic creation of articles inspired by '
         'our named voices (Becky Kennedy, Huberman, etc.). Original writing with '
         'proper attribution. 4-6 articles per category to start.'),
        ('Cost controls', 'Per-family daily spending caps on AI usage. One bored kid '
         'overnight should not generate a $4,000 bill.'),
        ('Homeschool market research', 'Heather\'s action item: demographic data on '
         'homeschooling families (~25% in Greg\'s area). Potential high-value segment.'),
    ]
    for title, desc in important:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('Future (after beta feedback)', level=2)
    future = [
        'COPPA compliance build-out (the amended rule is now in force — see Section 12; '
        'required before any public kid-facing launch)',
        'Dark mode',
        'Android version',
        'The senior-focused communication app (side concept from the meeting—'
        'simple, two-button, face-recognition FaceTime for grandparents)',
    ]
    for f in future:
        doc.add_paragraph(f, style='List Bullet')

    add_horizontal_rule(doc)

    # === SECTION 9: BETA LAUNCH PLAN ===
    doc.add_heading('9. Beta Launch Plan', level=1)

    doc.add_heading('Target', level=3)
    doc.add_paragraph(
        'Fall 2026—by the start of the next school year. 25–50 users from our immediate '
        'circles. Closed beta: invite-only, informed-consent agreement signed in-app.'
    )

    doc.add_heading('Goal', level=3)
    doc.add_paragraph(
        'Demonstrate the concept to real families. Gather feedback. Prove to potential '
        'investors that the product works and people want it. "Just enough to be dangerous"—'
        'a smooth experience that hooks users on the primary value without being feature-complete.'
    )

    doc.add_heading('Success criteria', level=3)
    criteria = [
        'Parents complete onboarding and return to the app within 48 hours.',
        'Kids have at least one multi-turn voice conversation with their companion.',
        'Zero undetected crisis events (safety system works as designed).',
        'Parents report feeling "less alone" in qualitative feedback.',
        'The experience is smooth enough to demo to an investor without caveats.',
    ]
    for c in criteria:
        doc.add_paragraph(c, style='List Bullet')

    doc.add_heading('What "not COPPA-compliant" means for beta', level=3)
    doc.add_paragraph(
        'The closed beta operates under direct parental consent (parent signs up, parent '
        'gives the device to the child). This is legal for a closed test. It is NOT legal '
        'for a public App Store listing marketed to children under 13. The COPPA decision '
        '(teen-only public launch vs. full compliance for under-13) happens after beta data '
        'tells us which audience had the strongest engagement.'
    )

    add_horizontal_rule(doc)

    # === SECTION 10: DECISIONS FROM MEETING ===
    doc.add_heading('10. Decisions from Our First Meeting', level=1)
    doc.add_paragraph('June 5, 2026 — Miguel, Heather, Greg')

    doc.add_heading('Aligned', level=2)
    aligned = [
        ('Family and child agent architecture defined.', 'A main family agent for parents '
         'alongside separate, age-appropriate agents for individual children.'),
        ('Shared workspace.', 'Google Drive for documentation and product backlog. '
         'Figma for design collaboration and engineering handoff.'),
        ('Tablet support in scope.', 'iPad experience for the handoff. Parents give '
         'tablets to kids, not phones.'),
        ('Beta launch target: fall 2026.', 'By the next school year. 25–50 users.'),
        ('Small team, focused product.', 'Don\'t try to do everything. Nail the '
         'core experience first.'),
        ('No feed-based UI.', 'Spatial, minimal, "lean-in" design. Not TikTok for parents. '
         'Intentional use, not doom-scrolling.'),
        ('Meeting cadence.', 'Thursdays, 9–10am. Weekly.'),
    ]
    for title, desc in aligned:
        p = doc.add_paragraph()
        run = p.add_run(title + ' ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('Needs further discussion', level=2)
    doc.add_paragraph(
        'Children\'s AI agent feature strategy. The kid companion is built and working, '
        'but the team needs to align on the specific user-facing framing: what do we call it, '
        'how do we explain it to parents who might be nervous about AI + kids, and what are '
        'the age-appropriate interface differences (a 4-year-old\'s experience vs. a 12-year-old\'s).'
    )

    doc.add_heading('Action items', level=2)
    actions = [
        '[Heather] Research homeschooling demographics and market sizing.',
        '[Miguel] Set up shared Google Drive workspace with existing docs + product backlog.',
        '[Greg] Create Figma project. Upload current TestFlight screenshots. Map user journeys. '
        'Identify dead ends.',
        '[Greg] Share Happily pitch decks with Heather (storytelling reference).',
        '[Heather] Share audience persona research with Greg.',
        '[Greg] Research Wendelberry (agricultural/community business model reference).',
        '[Heather] Share farming/Ecology Center resources with Greg.',
        '[Heather] Review Mobin design resource for UI flow patterns.',
        '[All] Thursday 9am follow-up meeting.',
        '[All] Keep Miguel focused on core development, not tangential features.',
    ]
    for a in actions:
        doc.add_paragraph(a, style='List Bullet')

    add_horizontal_rule(doc)

    # === SECTION 11: MARKET OPPORTUNITY ===
    doc.add_heading('11. Market Opportunity', level=1)

    doc.add_paragraph(
        'The following is a structured overview of the addressable market for an AI-powered '
        'family companion. This data supports GTM planning and investor conversations.'
    )
    refresh = doc.add_paragraph()
    run = refresh.add_run('July 2026 refresh. ')
    run.bold = True
    run.font.color.rgb = OLIVE_DARK
    refresh.add_run(
        'A full deep-research pass (two companion documents in the GTM folder: the market '
        'research report and its activity-portfolio expansion) sharpened this picture with '
        'sourced proof-of-budget numbers: Good Inside (Dr. Becky) passed $34M revenue in 2025 '
        'with 100,000+ subscribers at ~$276/yr; OurFamilyWizard serves ~1M+ families at '
        '$150–300 per parent per year (often court-mandated); Skylight reports 9.3M users and '
        '99% year-over-year revenue growth; the average sports family spends ~$1,000+ per '
        'child per year and 25% of camp parents planned to spend over $2,000 per child in '
        '2025. The co-parenting segment is projected to be the fastest-growing slice of the '
        'parenting-app market. Those documents supersede the estimates below where they '
        'conflict; the figures in this section are kept for continuity.'
    )

    doc.add_heading('US market', level=2)
    doc.add_paragraph(
        '73 million children ages 0-17. Approximately 63 million adults are parents of '
        'minor children across ~35 million households. 91% of US adults own a smartphone. '
        '65-75% of parents already use at least one parenting-related app (pregnancy trackers, '
        'baby monitors, family calendars, or advice apps).'
    )

    doc.add_heading('Market sizing', level=3)
    market_data = [
        ('Global parenting apps', '$1.7B (2025) → $3.1B (2030), 12.8% CAGR'),
        ('US parenting apps (est. 40% of global)', '~$680M (2025)'),
        ('Family safety/parental control software', '$2.5B (2025) → $4.9B (2030), 14.5% CAGR'),
        ('AI in education (global)', '$7B (2025) → $137B (2035), 34.5% CAGR'),
        ('AI consumer apps (total spending)', '$3-5B (2024), growing >100% year-over-year'),
    ]
    for label, value in market_data:
        p = doc.add_paragraph()
        run = p.add_run(label + ': ')
        run.bold = True
        p.add_run(value)

    doc.add_heading('Key segments', level=3)
    segments = [
        ('Dual-income households', '~16M families. Highest willingness-to-pay ($10-20/month). '
         'Time is the scarcest resource. "Mental load reduction" is a premium value prop.'),
        ('Single parents', '~10M families. High need for organizational tools, price-sensitive. '
         'Co-parenting coordination (custody schedules, handoff logistics) is a premium upsell.'),
        ('Homeschooling families', '3.4M students (up 36% from 2019). Heavy digital curriculum '
         'consumers. Need scheduling and portfolio tracking tools that assume non-standard schedules.'),
        ('Special needs parents', '~5.5M families (7.5M students served under IDEA). '
         'Massively underserved. 5-10x more coordination required. Extremely high engagement '
         'when they find a tool that works.'),
        ('Military families', '~1M families with children. Relocate every 2-3 years. '
         'Acute need for schedule re-building and community discovery in new locations.'),
        ('Grandparents raising grandchildren', '2.4M in the US. Growing segment. '
         'Rarely targeted by parenting apps despite high need.'),
    ]
    for title, desc in segments:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('English-speaking worldwide', level=2)
    doc.add_paragraph(
        'Total addressable English-speaking parents: ~125-135 million '
        '(US 63M + UK 12M + Canada 5.4M + Australia 3.8M + New Zealand 0.75M + '
        'India English-speaking segment ~40-50M). '
        'UK/Canada/Australia mirror US app-spending patterns ($10-15/month comfort zone). '
        'India\'s English-speaking parents (urban, educated, smartphone-first) represent '
        'a massive secondary market at a lower price point ($2-5/month).'
    )

    doc.add_heading('Spanish-speaking worldwide', level=2)
    doc.add_paragraph(
        'Total addressable Spanish-speaking parents: ~65-75 million across Mexico, '
        'Colombia, Argentina, Spain, Peru, Chile, and the rest of Latin America. '
        'Smartphone penetration is high (83-97% in top markets). App subscription '
        'willingness is lower ($2-5/month) but growing rapidly as digital payment '
        'infrastructure improves.'
    )
    doc.add_paragraph(
        'Critical insight: there is no dominant AI-powered parenting app in Spanish. '
        'Kinedu ($17M raised, Monterrey-based) is the closest competitor but focuses '
        'narrowly on early childhood development. BabyCenter en Espanol dominates '
        'content but is ad-supported, not AI-native. This is clear whitespace.'
    )
    doc.add_paragraph(
        'Cultural advantage: Latin American family structures (multi-generational, '
        'extended-family involvement, community-oriented) align naturally with our '
        'inclusive "caregivers not parents" architecture. WhatsApp-group parenting advice '
        'is the dominant pattern—our community features map directly to this behavior.'
    )

    doc.add_heading('Bottom-up TAM estimate', level=2)
    tam_table = doc.add_table(rows=7, cols=4)
    tam_table.style = 'Table Grid'
    headers = ['Segment', 'Parents', 'Conversion', 'Annual Revenue']
    for i, h in enumerate(headers):
        cell = tam_table.cell(0, i)
        cell.text = h
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(cell, 'E8EBDC')

    tam_rows = [
        ('US dual-income (premium)', '16M', '5%', '$96M'),
        ('US all parents (core)', '63M', '3%', '$113M'),
        ('US single parents', '10M', '2%', '$8M'),
        ('US homeschooling', '3.4M', '8%', '$27M'),
        ('English worldwide (ex-US)', '62-72M', '2%', '$74-86M'),
        ('Spanish worldwide', '65-75M', '2%', '$39-45M'),
    ]
    for row_idx, (seg, parents, conv, rev) in enumerate(tam_rows, 1):
        tam_table.cell(row_idx, 0).text = seg
        tam_table.cell(row_idx, 1).text = parents
        tam_table.cell(row_idx, 2).text = conv
        tam_table.cell(row_idx, 3).text = rev
        for col in range(4):
            tam_table.cell(row_idx, col).paragraphs[0].runs[0].font.size = Pt(9)

    doc.add_paragraph()
    doc.add_paragraph(
        'Total addressable market across all segments: $350-400M at conservative '
        'penetration assumptions. With the AI consumer app market growing >100% YoY '
        'and no category leader in AI-powered family tools, the realistic serviceable '
        'obtainable market (SOM) at scale is $50-200M ARR in the US, '
        '$100-400M globally across English + Spanish markets.'
    )

    doc.add_heading('Why now', level=3)
    why_now = [
        'AI capability inflection: GPT-4+ class models make personalized parenting '
        'coaching viable for the first time (not possible before 2023).',
        'Cultural readiness: "mental load" and "invisible labor" are mainstream vocabulary. '
        'The market is primed for a solution.',
        'Market white space: no AI-native parenting app has achieved category leadership. '
        'Incumbents are content platforms (BabyCenter) or single-purpose utilities (Cozi).',
        'Bilingual advantage: 65-75M Spanish-speaking parents are underserved by any '
        'comparable AI product.',
        'Diverse family structures: existing products assume nuclear families. We don\'t. '
        'That\'s a wedge into every underserved segment.',
    ]
    for w in why_now:
        doc.add_paragraph(w, style='List Bullet')

    add_horizontal_rule(doc)

    # === SECTION 12: GO-TO-MARKET STRATEGY ===
    doc.add_heading('12. Go-To-Market Strategy', level=1)

    doc.add_paragraph(
        'Added July 2026; revised after a five-persona adversarial review of the strategy '
        '(verdict: reshape) plus a verification research pass. The full evidence trail lives '
        'alongside this document in the GTM folder — gtm-strategy.md is the canonical '
        'version of what follows. The strategy in one sentence: lead with one acute, '
        'seasonal logistics pain for one sharp audience — designed so it delivers full '
        'value even when only ONE parent participates — retain with the always-on '
        'ingestion loop and the registration-window watchlist, and validate demand with a '
        'funnel before building anything else.'
    )

    doc.add_heading('The wedge', level=2)
    doc.add_paragraph(
        'We cannot market a platform; strangers buy a fix for the one pain they feel today. '
        'Our entry point—the wedge—is activity and camp logistics for the load-bearing '
        'parent in a two-household family. It is acute (85% of parents report losing sleep '
        'over summer care and scheduling; 90% among working parents — Bright Horizons 2026 '
        'Modern Family Index), seasonal (predictable registration panics), budgeted '
        '(separated parents already accept $150–300/parent/yr for court-mandated '
        'co-parenting apps), and authentic (Miguel is the customer). Crucially, the product '
        'is SOLO-FIRST: one parent gets full value alone, and the other parent participates '
        'at zero friction—plain calendar invites and a magic forwarding email address, '
        'never an app install, never an account, never a charge. Retention comes from the '
        'always-on ingestion loop (school emails, flyers, registrations) and from watching '
        'registration windows—the product re-arms every season.'
    )

    doc.add_heading('Positioning statement', level=3)
    pos = doc.add_paragraph()
    run = pos.add_run(
        'For the parent who carries the logistics of raising kids across two households, '
        'MVP is the AI chief-of-staff that finds the camps, watches the registration '
        'windows, turns flyers and school emails into both homes\' calendars, and warns '
        'you before a coverage gap becomes a fight—and it works even when only one of you '
        'uses it. Unlike OurFamilyWizard and TalkingParents, which document conflict for '
        'court, MVP prevents it; unlike ChatGPT, it knows your family, your custody '
        'rhythm, and your deadlines.'
    )
    run.italic = True

    doc.add_heading('Why not lead with the coach or the companions', level=3)
    doc.add_paragraph(
        '"An AI that gives parenting advice" is ChatGPT with extra steps—Milo, a '
        'better-funded, OpenAI-endorsed family AI copilot, shut down in January 2026 in '
        'exactly that squeeze ("the technology is simply too early to be reliable in any '
        'useful way" — its founder\'s farewell post), and Good Inside already owns the '
        'coaching brand position. Worse, for OUR buyer the coach is a liability before '
        'it\'s a hook: AI chat logs carry no legal privilege and are discoverable in '
        'custody litigation, so a separated parent will not confide in a coach whose '
        'transcripts could surface in court. The coach therefore stays in the product as a '
        'supporting feature and out of the marketing until its zero-retention privacy '
        'architecture ships (see regulatory posture below). Our defensible moats are what '
        'generic AI structurally cannot do: a persistent family profile, agentic work '
        '(camp research, registration watching, flyer-to-calendar, Gmail and calendar '
        'sync), and two-household coordination.'
    )

    doc.add_heading('From camp planner to Activity OS (solving seasonality)', level=2)
    doc.add_paragraph(
        'Camp planning alone is a January–April business. The expansion research reframes it '
        'as one instance of a repeating job—discover, decide, register, coordinate the things '
        'my kids do—across five verticals that chain into a year-round relay. The engine we '
        'built (discovery agent, fit scoring, flyer vision, Gmail reading, calendar sync) is '
        'activity-type-agnostic; only the marketing entry point rotates.'
    )

    verticals_table = doc.add_table(rows=6, cols=3)
    verticals_table.style = 'Table Grid'
    vheaders = ['Vertical', 'Rhythm', 'Role']
    for i, h in enumerate(vheaders):
        cell = verticals_table.cell(0, i)
        cell.text = h
        cell.paragraphs[0].runs[0].bold = True
        cell.paragraphs[0].runs[0].font.size = Pt(9)
        set_cell_bg(cell, 'E8EBDC')
    vrows = [
        ('Camps + school-break coverage', '3–4 acute episodes/yr', 'The anchor and launch wedge'),
        ('Extracurriculars & youth sports', 'Weekly + 2 enrollment seasons', 'Highest family spend; makes it a weekly habit'),
        ('School life (emails, flyers, permission slips)', 'Daily in school year', 'The sleeper: 80+ school emails/mo; our ingestion pipeline already does this for camps'),
        ('Weekend & local outings', 'Weekly', 'Engagement and content ("it\'s my weekend with the kids")'),
        ('Trips & vacations', '1–3 episodes/yr', 'Custody-schedule-scoped only; never "AI trip planner"'),
    ]
    for row_idx, (v, r, role) in enumerate(vrows, 1):
        verticals_table.cell(row_idx, 0).text = v
        verticals_table.cell(row_idx, 1).text = r
        verticals_table.cell(row_idx, 2).text = role
        for col in range(3):
            verticals_table.cell(row_idx, col).paragraphs[0].runs[0].font.size = Pt(9)

    doc.add_paragraph()
    doc.add_paragraph(
        'Discipline rule: one agent with five entry doors, not five features on a homepage. '
        'The landing page always leads with whichever seasonal episode is next on the '
        'calendar (as of July: fall activity registration and the back-to-school email '
        'wave); the "your family\'s activity year" map is the reveal, never the pitch. '
        'This also strengthens pricing: the subscription is roughly 3% of the $3,000–5,000+ '
        'a two-kid activity family already spends on the things it coordinates.'
    )
    status = doc.add_paragraph()
    run = status.add_run('Status, July 11: this table is no longer a roadmap. ')
    run.bold = True
    status.add_run(
        'All five verticals are live in production behind one agent, built in a single '
        'week-long push and hardened by an adversarial three-critic design review, '
        'live-model evaluation gates, and end-to-end tests against real AI on every '
        'vertical. The engine was activity-type-agnostic as promised: the fifth vertical '
        '(trips) required zero new instrumentation and zero client changes. When fall '
        'registration season arrives, the product the ads describe already exists.'
    )

    doc.add_heading('Three design commitments from the adversarial review', level=2)
    doc.add_paragraph(
        'In July 2026 we ran the strategy through a five-persona adversarial council '
        '(skeptic, optimist, first-principles analyst, market researcher, and a role-played '
        'buyer), then fact-checked its load-bearing claims at primary sources. It confirmed '
        'the wedge and forced three product commitments:'
    )
    commitments = [
        ('1. Solo-first, zero-friction second parent.', 'The single biggest failure mode '
         'in this category is "my ex won\'t use the app"—so common the incumbents publish '
         'help articles about it, and their only remedy is a court order. Our answer is '
         'design, not litigation: parent #1 gets full value alone; parent #2 participates '
         'by accepting ordinary calendar invites and forwarding emails to a magic '
         'address—no install, no account, no cost. No co-parenting product on the market '
         'does frictionless inclusion (their "solo modes" mean documenting unilaterally '
         'for court). The positioning line: "the logistics work even when only one of '
         'you does."'),
        ('2. The registration-window watchlist (the "spot-getter") — SHIPPED July 11.', 'The '
         'sharpest camp pain is not choosing—it\'s getting a SPOT: popular registrations '
         'sell out in minutes, parents set alarms and trade dates in group chats, and no '
         'national parent-side product watches registration-open windows (the only entrant '
         'is a manual, single-metro database). "We watch the registration dates near you, '
         'alert you before they open, and have your details ready" turns our discovery '
         'agent from list-maker into spot-getter—and re-arms the product every season, '
         'which is the honest retention engine. This is now LIVE: reminders 7 days ahead '
         'and before the window opens (never after), researched dates labeled as estimates '
         'until the parent confirms, and an internal alarm that fires if we ever miss one—'
         'because the promise is only worth making if we can keep it at 100%.'),
        ('3. Split data model: durable logistics, zero-retention coach.', 'Co-parenting '
         'incumbents SELL discoverability (court-certified records; published subpoena '
         'fee schedules), and family-law attorneys now warn divorcing clients that AI '
         'chat logs are discoverable and carry no privilege. So we split the product\'s '
         'data in two and say so loudly: logistics data (calendar, activities, handoffs) '
         'is durable, exportable, yours; the AI coach runs zero-retention—no server-side '
         'transcripts, nothing to produce. Honest copy only: this reduces exposure, it '
         'does not create legal privilege. No family app occupies this position today.'),
    ]
    for title, desc in commitments:
        p = doc.add_paragraph()
        run = p.add_run(title + ' ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('Who we acquire first (beachhead personas)', level=2)
    personas = [
        ('The two-home logistics dad', '35–48, divorced or separated, shared custody, kids '
         '3–12. Already pays for OurFamilyWizard (often court-ordered). Trigger: camp season, '
         'a missed activity that caused conflict. Miguel\'s mirror—and the founder story is '
         'the content engine.'),
        ('The maxed-out coordinating mom', '32–45, dual-income, primary logistics owner, '
         'carries the mental load (mothers carry ~67% more household to-do items — Univ. of '
         'Bath, 2025). Trigger: the spring camp-planning panic and the 40-tab spreadsheet. '
         'Heather is this persona—she lives it daily with her 9- and 5-year-old girls—so '
         'this segment, like the first, gets a founder\'s authentic voice.'),
        ('The newly separated parent', 'In the acute chaos phase; highest willingness to '
         'adopt a new system; reachable through attorneys, mediators, and therapists—a '
         'referral channel we will pilot.'),
    ]
    for title, desc in personas:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('Pricing hypothesis (to be tested, not assumed)', level=2)
    doc.add_paragraph(
        'Test range: $99–$149 per family per year, with $199 kept as the top '
        'willingness-to-pay bucket to measure headroom. One subscription covers the '
        'family; the second parent is genuinely free forever. The adversarial review '
        'corrected our original $199 anchor: court-ordered parents can\'t cancel '
        'OurFamilyWizard, so we are additive to that spend, not a replacement—our real '
        'price competition is the AI family-assistant market, which clusters at $39–99/yr '
        '(Ohai $99, Nori ~$96, Skylight Plus $79). Anchor the copy against the activity '
        'budget ("~3% of what you already spend on the things it coordinates") and the '
        'prevented scramble week, never against OFW. Hard paywall with a trial rather '
        'than freemium (RevenueCat 2026: ~5x conversion, near-identical retention), plus '
        'a seasonal risk-reversal in year one ("full refund before September 1—if it '
        'doesn\'t survive one real summer, you pay nothing"). The funnel\'s '
        'willingness-to-pay question sets the final number, segmented by household '
        'structure.'
    )

    doc.add_heading('The validation funnel (the next 90 days)', level=2)
    doc.add_paragraph(
        'Both playbooks we studied agree: validate demand before building more. Two engines '
        'run in parallel, both feeding one email list.'
    )
    funnel_items = [
        ('The Family Snapshot quiz', 'Our 8-step onboarding, ported to a public landing '
         'page as a quiz. Email capture at question 3–4; a friction question whose answer '
         'options map to the five verticals (so respondents vote on our headline for us); '
         'a household-structure question ("does your kids\' other parent live with '
         'you?")—the single most valuable segmentation of the willingness-to-pay data; '
         'the willingness-to-pay question; and a genuinely useful AI-generated payoff: '
         'each kid\'s stage, named friction points, three things to try this week, and a '
         '12-month map of the family\'s activity year. Free to generate; the full version '
         'requires an account. This is simultaneously the lead magnet, the pricing test, '
         'and a live product demo.'),
        ('Paid truth serum', '~$20/day of Meta ads for two weeks, pixel firing only on '
         'email capture, 5–8 hooks tested. The flagship creative: snap a photo of the '
         'field-trip flyer, and the permission-slip task, the fee to-do, and the date land '
         'on both parents\' calendars in five seconds—visual, verifiable, unfakeable. Two '
         'hooks from the adversarial review join the set: "it watches registration-open '
         'dates so you don\'t have to set alarms" and "works even if your ex never '
         'installs it—they just get calendar invites."'),
        ('Founder-led content — two voices', 'Daily educational posts for 30 days, split '
         'across two authentic founder voices: Miguel on the divorce-dad / two-household '
         'angle, Heather on the mental-load / coordinating-mom angle. Between them the '
         'founders embody both beachhead personas first-hand, and their kids\' ages '
         'overlap (roughly 4–5 and 9–10), so every stage-specific topic—bedtime for the '
         'little one, activities and friendships for the big kid—is lived experience, '
         'told from two household structures. Same playbook as Dr. Becky / Big Little '
         'Feelings: give away genuinely useful material and the audience compounds into '
         'demand. No selling—one line pointing to the Snapshot. Two voices also halves '
         'the per-person cadence needed to stay daily.'),
        ('Early-access cohort', 'The warmest leads become founding families: a lifetime '
         'discount (~$99/yr locked for life vs. $199 standard) in exchange for daily '
         'feedback—early product champions, not revenue.'),
    ]
    for title, desc in funnel_items:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('Decision gates (numbers, not vibes)', level=3)
    gates = [
        'Gate zero, before any ad spend (48 hours, under $50): message 25 separated '
        'parents with the solo-first pitch. Pass = at least 5 would pay ~$10/mo AND at '
        'least 15 believe zero-friction ex participation (invites + email forwarding) '
        'would actually happen in their situation. Fail the second condition → lead with '
        'the maxed-out-mom persona instead of the co-parent angle.',
        '200 emails by day 30, or the offer/messaging is wrong (pivot the hook before '
        'abandoning the wedge).',
        'Median willingness-to-pay ≥ $100/yr green-lights the paid cohort; $50–99 means '
        'reprice and re-message; below $50 means rethink the wedge.',
        'Cost per email ≤ $3–5 after creative iteration, or paid is shelved in favor of '
        'organic + referrals.',
        'If one non-camp vertical wins the quiz friction vote by more than 2x, the '
        'headline changes—the product doesn\'t have to.',
        'Sports-registration claims stay out of ads until the discovery agent\'s hit-rate '
        'is validated in 2–3 metro areas.',
    ]
    for g in gates:
        doc.add_paragraph(g, style='List Bullet')

    doc.add_heading('Regulatory posture and trust', level=2)
    doc.add_paragraph(
        'We market a PARENT-FACING tool, full stop. The kids\' voice companion stays out of '
        'all GTM until compliance and legal review are complete: the amended COPPA rule is '
        'now in force (compliance date April 22, 2026—voiceprints are now "personal '
        'information," AI training requires separate verifiable parental consent, indefinite '
        'retention is banned), and the FTC opened a formal inquiry into companion chatbots '
        'and children in September 2025. Regardless of marketing, we build the compliance '
        'kit: age gates, consent flows, a written retention policy, and data deletion. '
        'Trust is also a moat we can buy cheaply: one named clinical/child-development '
        'advisor, a public evidence-and-methodology page, and a plain-language safety and '
        'data page—which now also states the split data model from design commitment #3 '
        '(durable, exportable logistics data; zero-retention coach). The first brick is '
        'laid: a public, no-login "How MVP works" docs site now ships with the product—'
        'thirteen illustrated pages including plain-language pages on the coach and the '
        'kids\' companions (consent, moderation, crisis lock, parent-visible transcripts). '
        'Social proof is never fabricated—until real testimonials exist (with consent), '
        'we borrow authority from cited research and the founder story.'
    )

    doc.add_heading('Honest ceiling and what raises it', level=2)
    doc.add_paragraph(
        'Modeled scenarios put the base case around $250–300K ARR at 24 months (roughly '
        '1,800–2,200 paying families at $129)—a strong independent business, not yet a '
        'venture story. Three '
        'things upgrade it: funnel proof that acquisition cost is far below lifetime value; '
        'a camp-booking marketplace take-rate on top of the discovery agent; and B2B2C '
        'channels (family-law mediators and therapists, employers/EAPs, pediatricians) that '
        'de-risk churn the way court mandates de-risk OurFamilyWizard\'s. We do not raise '
        'money before the funnel produces those numbers—our AI-augmented build speed means '
        'we can reach revenue cheaply.'
    )

    doc.add_heading('The 90-day sequence', level=3)
    ninety = [
        ('Weeks 1–2 — falsify cheap, instrument the truth.', 'Run gate zero (the 25-parent '
         'solo-first test); harvest verbatim parent language from Reddit/Facebook into a '
         'swipe file; ship the Family Snapshot funnel with the fall-registration lead; '
         'publish the evidence + safety/data pages; approach one advisor.'),
        ('Weeks 3–6 — run both engines.', 'Meta ads at $20/day; daily founder content in '
         'two voices (Miguel and Heather, alternating); drive toward the 200-email bar and '
         'the WTP read; recruit the founding-family cohort from the warmest leads. In '
         'parallel, small funnel-informed product work: the zero-friction parent-#2 flow. '
         '(The registration-window watchlist, originally slotted here, shipped ahead of '
         'schedule on July 11 and is live in production.)'),
        ('Weeks 7–12 — convert and decide.', 'Founding-family lifetime deal with daily '
         'feedback; hard-paywall trial plus the September-1 risk reversal; first real '
         'testimonials; pilot outreach to 3–5 family-law mediators/therapists. Then the '
         'gates decide what we do next.'),
    ]
    for title, desc in ninety:
        p = doc.add_paragraph()
        run = p.add_run(title + ' ')
        run.bold = True
        p.add_run(desc)

    add_horizontal_rule(doc)

    # === CLOSING ===
    doc.add_paragraph()
    closing = doc.add_paragraph()
    closing.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = closing.add_run('This is ground zero. The foundation is built. The team is assembled. '
                          'The window is open. Now we ship.')
    run.font.italic = True
    run.font.color.rgb = OLIVE_DARK
    run.font.size = Pt(12)

    doc.add_paragraph()
    footer = doc.add_paragraph()
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = footer.add_run('MVP — June 2026, rev. July 12, 2026')
    run.font.size = Pt(10)
    run.font.color.rgb = INK_MUTED

    # Save
    out_path = os.path.join(os.path.dirname(__file__), 'MVP-Ground-Zero.docx')
    doc.save(out_path)
    print(f'Saved: {out_path}')
    return out_path


if __name__ == '__main__':
    create_doc()
