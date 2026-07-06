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
    run = meta.add_run('June 2026\nMiguel Alvarado, Heather Hannan-Kramer, Greg Harris')
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
         'cultural background. Two paths: structured form or conversational chat with the AI.'),
        ('Parent coaching agent', 'An AI assistant that remembers your family, adapts to your '
         'parenting style, and gives concrete, actionable advice. Not generic—it knows '
         'your kid\'s age band, your co-parenting situation, your stressors.'),
        ('Kid companion agents', 'One AI companion per child, automatically generated from '
         'the parent\'s profile. Age-appropriate personality. Voice-first interaction '
         '(the child speaks, the companion speaks back). Parent writes a "letter" that '
         'defines boundaries and personality.'),
        ('Content library', 'Editorial articles organized by topic. Community posts from '
         'other parents. Saved articles. Tag-based filtering.'),
        ('Handoff mode', 'Parent pins a kid companion, hands the device to the child. '
         'A curtain covers the parent UI. Child interacts only with their companion.'),
    ]
    for title, desc in items:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('The backend (deployed on Railway)', level=2)
    items = [
        ('AI agent pipeline', 'Powered by OpenAI\'s latest model (GPT-5.2). Each kid companion '
         'runs through a multi-stage pipeline: prompt synthesis (builds the system prompt from '
         'the parent\'s letter + kid profile), then streams responses through a real-time '
         'moderation pipeline.'),
        ('Five-layer moderation', '50+ crisis keyword patterns, OpenAI content moderation API, '
         'age-appropriateness classifier, streaming token-by-token moderator, and a final '
         'output check. If anything triggers, the conversation freezes immediately.'),
        ('Crisis detection', 'Self-harm, abuse, and suicide language triggers an instant '
         'parent notification, conversation lock, and crisis resources displayed to the child. '
         'The agent cannot be restarted until the parent explicitly intervenes.'),
        ('Voice pipeline (v2 in progress)', 'Real-time voice via ElevenLabs Conversational AI. '
         'WebRTC audio—under 150ms latency from the child speaking to the companion responding. '
         'The child just talks; no typing required.'),
        ('Intelligent family profile', 'Every interaction—parent coaching session, kid conversation, '
         'onboarding answer—feeds back into a living profile of the family. The system learns '
         'parenting style, kid temperaments, recurring challenges, and communication patterns '
         'over time. This isn\'t a static form you fill out once; it\'s a profile that gets '
         'smarter with every conversation, so the advice gets more relevant the longer you use it.'),
        ('Content management system', 'A web-based editor for creating and organizing articles, '
         'categories, and community posts. Used internally to manage the content library.'),
    ]
    for title, desc in items:
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

    doc.add_heading('Must-ship for beta', level=2)
    must_ship = [
        ('Real user identity', 'Replace the current name-based login with Apple Sign-In or '
         'a real account system. Two parents named "Miguel" must not collide. This is the '
         'single biggest blocker for putting real families on the app.'),
        ('Voice v2 (in progress)', 'Complete the ElevenLabs Conversational AI integration. '
         'Sub-150ms latency voice for kid companions. Currently 80% done—backend complete, '
         'iOS SDK integrated, wiring into the view layer is the remaining work.'),
        ('Crisis parent notification', 'When a kid companion detects a crisis, the parent '
         'currently gets a Slack alert (internal). Before beta, this must be a real push '
         'notification to the parent\'s device.'),
        ('Onboarding polish', 'Low-friction, drip-style information collection. Don\'t ask '
         'for everything upfront. Let the app learn the family over time. Greg\'s WeTransfer '
         'insight: one simple action to start.'),
        ('Design review & dead ends', 'Greg will map the current user journeys in Figma, '
         'identify "dead ends" where the user gets stuck, and propose solutions.'),
    ]
    for title, desc in must_ship:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('The parenting agenda manager (next major feature)', level=2)
    doc.add_paragraph(
        'This is the second pillar of the product after the companion agents. Where the '
        'coaching agent helps you think, the agenda manager helps you act. It\'s the agent '
        'that makes sure nothing falls through the cracks.'
    )
    agenda_items = [
        ('Proactive discovery', 'Scans for upcoming camps (summer, winter, spring break), '
         'classes, events, and activities relevant to each child—based on their age, '
         'interests, and your location. Surfaces options before registration deadlines close, '
         'not after.'),
        ('Email and message extraction', 'With permission, reads the parent\'s email and text '
         'messages to find event information that\'s already there: school newsletters with dates, '
         'coach emails with practice schedules, camp confirmations with packing lists, '
         'permission slips with deadlines. Pulls the signal out of the noise.'),
        ('Family calendar', 'Builds a unified calendar for the whole family—every kid\'s '
         'activities in one view. Syncs to Google Calendar so it lives where the parent '
         'already looks. No separate app to check.'),
        ('Reminders and to-dos', 'Manages the invisible labor: "Soccer registration closes '
         'Friday." "Pack sunscreen for field trip Monday." "Submit immunization form by the 15th." '
         'The kind of tasks that live in a parent\'s head rent-free until they\'re missed.'),
    ]
    for title, desc in agenda_items:
        p = doc.add_paragraph()
        run = p.add_run(title + '. ')
        run.bold = True
        p.add_run(desc)

    doc.add_paragraph()
    doc.add_paragraph(
        'This is the "Superhuman for family scheduling" concept—but smarter, because it '
        'knows your family profile. It doesn\'t suggest teen coding camp for your 4-year-old. '
        'It doesn\'t remind you about a deadline that\'s already passed. It acts like the '
        'hyper-organized parent friend who somehow always knows what\'s coming up and texts '
        'you "hey, did you sign up for X yet?"'
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
        'Go-to-market strategy and growth channels',
        'COPPA compliance (required for public launch if under-13 audience)',
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
    run = footer.add_run('MVP — June 2026')
    run.font.size = Pt(10)
    run.font.color.rgb = INK_MUTED

    # Save
    out_path = os.path.join(os.path.dirname(__file__), 'MVP-Ground-Zero.docx')
    doc.save(out_path)
    print(f'Saved: {out_path}')
    return out_path


if __name__ == '__main__':
    create_doc()
