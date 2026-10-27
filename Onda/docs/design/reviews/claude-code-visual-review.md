# Onda Concept 04 ("Wonder into practice", softened palette): independent visual critique

I inspected the actual pixels. The parts I'd keep are the four phone headlines, the dark-on-terracotta buttons, the strong wordmark and the attunement pose. As a direction it is good, but it is not yet the strongest we can make. Its weakest spot is the Understand screen, which states a guess about the child as a fact. That is a product problem, not a styling one.

## 0. What I inspected

**File**
- `Onda/docs/design/reviews/assets/onda-concept-04-wonder-into-practice.png`.
- I recomputed the SHA-256 locally: `8260e738…97806`. That matches the coordinator's hash. Size is 2,133,766 bytes.
- The PNG header says 1536×1024, 8-bit RGB.

**How I looked at it**
- I viewed the full image, plus my own crops of the icon (2×), the caregiver illustration (2×) and phone 3 (2×). I also made 32 px and 16 px box-averaged downsamples of the icon.
- I measured pixels with a read-only, standard-library-only Python PNG decoder. PIL isn't installed, and I installed nothing.
- My crops and the script sit in `$TMPDIR/onda-px/` (scratch only, not the repo). I did not change the asset.

**Two concrete visible details (proof of inspection)**
1. Phone 1 reads "01 / NOTICE · What happened? · [pink card] Getting out the door felt hard. · We were late. I rushed. My child hid their shoes." Below that is a terracotta pill button, "Look a little closer", with dark text.
2. Lower left is a crouching adult with deep brown skin, curly hair in a bun, a gold hoop earring, a white T-shirt, **saturated violet trousers** and white sneakers. Her chin rests on her hand, mirroring a curly-haired child in a yellow T-shirt crouched opposite. Above them is a handwritten caption, "Different perspectives open new possibilities", next to a magnifying glass framing a sprig.

**Other things I observed directly**
- Palette swatches labelled IVORY, AUBERGINE, **ORANGE**, LILAC, CHARTREUSE. The swatch is called "orange", not terracotta.
- Headline: "The wonder to understand. The clarity to act."
- Upper-right handwritten note: "Smaller shifts. Brighter days."
- Phone 2: "02 / UNDERSTAND · What else could be true? · [lilac card] Leaving a good moment can be hard. · Could a little warning make the next goodbye easier?" Button: "Find one thing to try".
- Phone 3: "03 / TRY · Make room for goodbye. · Before leaving, offer a two-minute warning and one last thing to finish." Below it, an outlined card: "LATER / REFLECT · What did you notice? ›". Button: "I'll try this".
- A progress row under the phones: Notice → Understand → Try → Reflect, with lilac, terracotta, chartreuse and violet dots and handwritten labels.
- Footer: "DESIGN EXPLORATION • NOT A FINAL IDENTITY" and "ONDA / OCT 2026".

**Labels used below:** **[O]** observed pixels, **[M]** measured, **[I]** inference, **[H]** hypothesis that needs a test.

## 1. Strongest elements worth keeping

1. **The copy on the phones is the best part of the board.** [O] "What happened?", then "What else could be true?", then "Make room for goodbye." [I] The questions invite curiosity instead of passing judgment, and they move from noticing to reframing to one small, parent-controlled change in timing. Reflect is an open question, "What did you notice?", with no score, streak, tick or mood face. [O] I saw no scoring anywhere, which confirms my earlier no-score check.
2. **Phone 1 keeps feeling and fact apart.** [O] The parent's feeling ("felt hard") sits in a tinted card. The facts ("We were late. I rushed. My child hid their shoes.") sit in plain body text below. [I] This already starts the layering the product brief asks for. "I rushed" is honest self-attribution without blame, which is exactly "how I show up."
3. **Expression around the edges, calm in the middle.** [O] The phone screens are mostly flat ivory with one display headline, one card, short body text and one pill button. The collage stays mostly in the outer board. [I] That is the right split for "fun but professional editorial."
4. **The wordmark.** [O] A heavy, high-contrast serif "Onda" with tight spacing. [I] It is confident and editorial, and it reads at both board scale and the in-app header scale. Of all the brand pieces, it scales best (see §9).
5. **The buttons.** [M] Dark text on terracotta measures about 8.0–8.2:1 on all three phones. Choosing dark text over white matters: white or ivory on this terracotta would be about 2.4:1. Keep that rule.
6. **The attunement pose.** [O] Adult and child crouch at eye level, mirroring each other. [I] This shows "being on the same wavelength" better than the icon does.

## 2. Top five problems, tied to what is visible

| # | Severity | Problem | Visible evidence | Fix | Tradeoff |
|---|---|---|---|---|---|
| 1 | **High (product/trust)** | **Understand states a guess about the child as a fact, and offers only one guess.** | [O] Phone 1 says nothing about a "good moment". Phone 2's card asserts "Leaving a good moment can be hard." There is one card, no "maybe", no alternatives, no way to correct it. A sprig icon gives it a gentle authority. | Label it as a possibility ("Maybe: they were in the middle of something good"). Show 2–3 tappable alternatives plus "None of these / I'll say", and a small "It's a guess, you know them best." | More taps and slightly less polish, but it is the brief's central safety and differentiation claim. |
| 2 | **High (positioning)** | **Try ignores the parent's own part and gives generic tactic advice.** | [O] Notice includes "I rushed". Try offers "two-minute warning and one last thing to finish", a standard transition tip. Nothing goes back to the rushing. | Offer one adjustment for each lever: timing (warning), the parent's own pace or state ("slow my first sentence"), and the environment ("shoes by the door the night before"). Let the parent pick. | Less punchy than a single card. But a single tip is exactly what a general assistant gives, and the brief says Onda must beat that. |
| 3 | **Medium-high (flow completeness)** | **Rehearse is missing and Reflect is only a footnote.** | [O] Only three phones. Reflect is a fourth dot outside the phones and a small "LATER / REFLECT" card. Nothing shows private rehearsal. | Add a fourth phone, "Practice saying it", with the actual words ("Two more minutes, then shoes"), and show Reflect as its own screen that accepts "it didn't land". | More board space; may have to drop the caregiver hero size (see the alternative in §11). |
| 4 | **Medium (brand coherence)** | **Too many taglines, and some are platitudes or promises.** | [O] Four messages compete: "Wonder into practice.", "The wonder to understand. The clarity to act.", "Different perspectives open new possibilities.", "Smaller shifts. Brighter days." [I] "Brighter days" implies an outcome promise. "Clarity" pulls against the uncertainty the product should model. The handwritten ones read like stock wellness copy. | Keep one tagline ("Wonder into practice" is the most distinctive). Cut "Brighter days". Turn one handwritten note into a real parent-voice line, e.g. "I rushed. They hid their shoes." | Loses some board decoration, gains sharper positioning. |
| 5 | **Medium (palette drift and contrast)** | **The "softened" palette isn't what the board actually uses, and small terracotta text is low-contrast.** | [O] The adult's trousers and the Reflect dot are a saturated violet [M ≈ `#A541CB` for the dot] that is not among the five swatches. [M] Small "01" numerals are about 3.3:1 at their darkest core and lighter at the antialiased edges. Lilac and chartreuse dots are about 1.5–1.7:1 on ivory. | Either add the violet as a named accent or pull it back to aubergine or lilac. Darken numerals to a text-only terracotta (aim for ≥4.5:1, not yet measured) or set them in aubergine. Never let dot color be the only signal of state. | A slightly less vivid board. The violet is part of why the illustration pops, so it is a deliberate choice, not a free fix. |

Lower-severity notes:
- **Decoration inside the app screens.** [O] Torn-paper collage and leaves fill the bottom of each phone, just above the button. Phone 2's leaves sit next to "easier?". [I] Real screens can't spare that space, and it will collide with longer copy (§3).
- **The magnifying glass.** [O] A magnifier framing a sprig. [I] The connotation is "examine the child", which grates against the brief's no-surveillance stance. A hand, an ear or the attunement loop would carry curiosity without inspection.
- **The wordmark repeats in every app header.** [O] "Onda" plus a back arrow on all three screens. [I] That is branding where navigation or context belongs ("Morning leaving"). Use the moment's title instead.
- **"I'll try this" is the only way forward.** [O] There is no "not now" or "smaller step" option, so the brief's low-capacity rule isn't shown.

## 3. Usability under stress and on small screens

- [O] Each screen holds one question, about two lines of text and one large pill button low on the screen, easy to reach one-handed. [I] That is good for a stressed parent.
- [O, measured on a downsample] At board scale the phones are about 270 px wide for roughly 390 pt of device width. The tracked uppercase micro-labels ("NOTICE", "LATER / REFLECT") have a cap height of about 7 board px, which I estimate (inference) at roughly 9–10 pt on a device. [H] That is too small for a quick glance during a hard moment.
- [H] With larger Dynamic Type sizes or on an iPhone SE, the two-line display headlines grow to 3–5 lines. With the decorative collage band, the Understand card and the button would push off-screen. A static board can't prove it either way.
- [I] Stress use is likely to happen *after* the episode, not during it. The board shows no quick-capture path (voice, one line, photo-free), so the most stressful entry point is missing.
- [O] The back arrow on step 01 means there is no clear exit or "save for later" on any screen.

## 4. Typography and readability

- [O] The display serif headlines are heavy, tightly spaced, and set over two lines in sentence case. Letters in "be true?" and "goodbye." nearly touch. [I] At hero size that looks expressive. At smaller sizes and in long phrases it will clog. Keep it for headlines of four words or fewer, and open the letter-spacing a little.
- [O] Body text is a humanist sans, dark on ivory, short line length. [M] About 17.9:1. Readable.
- [O] Small caps with wide letter-spacing sit next to a bold terracotta numeral. [I] The label/numeral pairing works as wayfinding, but the numeral is redundant, so its low contrast matters less than it would on the label itself.
- [O] Three type styles appear at once: display serif, humanist sans, handwritten script, plus tracked caps. [I] That is acceptable on a board but too much in the app. Keep the handwritten script off the product screens; it already stays off them.
- [I] This looks like a generated or flattened raster, so I can't confirm the font families, weights or tokens. Treat any specific typeface as not yet chosen.

## 5. Color contrast (measured on this raster)

**Method:** WCAG 2.x relative luminance. "Foreground" is the mean of the darkest 2% of pixels in the text box, which approximates the core ink colour. "Background" is the median of an adjacent patch.

**Limits:**
- Antialiasing makes thin or small strokes look lighter than the core value, so ratios for small text are optimistic.
- Paper texture adds roughly ±2–4 levels of noise.
- These are flattened raster samples, not design tokens.
- This is **not a compliance claim**.

| Pair | Sampled colours | Ratio |
|---|---|---|
| Swatch ivory vs swatch aubergine | `#F6ECDE` / `#2D0B32` | 14.9 |
| Swatch "orange" vs board ivory | `#DA9571` / `#FAF6EF` | **2.3** (fill only) |
| Swatch lilac vs board ivory | `#DAC2EC` / `#FAF6EF` | **1.5** |
| Swatch chartreuse vs board ivory | `#D8CB41` / `#FAF6EF` | **1.55** |
| Swatch "orange" vs aubergine | — | 7.1 |
| Button text vs terracotta fill (P1/P2/P3) | ≈`#03011A` / `#D79471` | 8.0–8.2 |
| Hypothetical ivory text on that terracotta | computed | **2.4**, so don't use it |
| "01" numeral core vs screen | `#C2795C` / `#FDFBF5` | **≈3.3** (edges lower) |
| "NOTICE" label vs screen | — | ≈19.8 (core; small text, so optimistic) |
| Phone 1 body vs screen | — | 17.9 |
| Phone 1 card text vs pink card | `#F8EFEA` bg | 18.0 |
| Phone 2 card text vs lilac card | `#EADEF0` bg | 15.8 |
| "LATER / REFLECT" vs card | `#201846` / `#FDF7F2` | 15.4 (core; small text, so optimistic) |
| Handwritten caption ink vs lilac paper | `#140D2D` / `#DBC9E9` | ≈12.0 |
| Progress dots vs ivory | lilac / terracotta / chartreuse / violet | 1.7 / 2.4 / 1.5 / 4.6 |

**What this means:**
- [I] Body text and interactive text look comfortable.
- [I] The risks are the terracotta numerals, which fall short for small text, and colour-only state dots.
- [I] Lilac and chartreuse must stay decorative on ivory.
- [O] The measured "orange" is `#DA9571`. That is close to, but not the same as, the supplied `#D58F72`, so source tokens are unverified.

## 6. Caregiver diversity and cultural fit

- [O] There is one caregiver: a femme-presenting adult with deep brown skin, natural curly hair and a gold hoop earring, with a child of similar skin tone and hair. Their warm, idealised, closed-eye smiles mirror each other.
- [I] Positive, non-stereotyped representation of a Black mother and child is a real strength. But a single figure makes "mom" the default caregiver. Fathers, grandparents, co-parents, foster or kinship carers, other ethnicities and visible disability are all absent.
- [I] The scene shows calm, idealised attunement while the copy is about a rushed, hidden-shoes morning. That tension edges toward the "perfect parent" image the brief wants to avoid. [H] Some parents will feel judged by the serenity.
- [O] No Spanish or bilingual cue appears anywhere. [I] Onda's intended bilingual warmth isn't expressed yet. That is fine since the name isn't final, but the bilingual claim is not supported by this board.

## 7. Distinctiveness versus generic wellness and editorial tropes

- [O] Textured flat-gouache figures, torn paper in lilac, chartreuse and terracotta, dark monstera-like leaves, a magnifying glass, handwritten notes, and an ivory/aubergine serif look.
- [I] Each of these is a common 2024–26 wellness/DTC trope (therapy apps, meditation, parenting newsletters). Softening the original neon orange took away the one unusual note. Visually, the board is pleasant but **not distinctive**.
- [I] What *is* distinctive is the questions on the phones and the four-verb loop. The brand should lean on the writing, which is where Onda differs, more than on the collage.

## 8. Learnability and product positioning

- [O] The numbered step labels plus the progress row make the loop easy to learn in seconds.
- [I] The board promises "understand → act" but shows the parent swapping a tip, not changing how they show up. The "I rushed" thread is dropped (problem #2). Without rehearse, alternative readings and correction (problems #1 and #3), it looks like a nicer general-assistant answer. That is exactly the comparison the brief warns about.
- [I] "Clarity to act" in the headline overstates certainty. "Wonder into practice" is more honest and more on-brand.

## 9. Icon and brand scalability

- [O] At 2×, the icon is two aubergine brush loops crossing, plus a terracotta loop and a lilac loop around a chartreuse dot, with three ink "spark" strokes. It reads as a four-petal flower, a propeller or an atom.
- [O, 32 px downsample] The shape survives but the terracotta and lilac loops wash into the ivory, and the sparks become stray specks.
- [O, 16 px downsample] It turns into a mushy blot with a yellow centre.
- [I] It doesn't say "wave" or "same wavelength", and the brush texture doesn't scale. The terracotta squiggle with a single loop between the two figures is a better "onda" mark than the icon itself.
- [I] Recommendation: a single-weight aubergine wave with one curiosity loop, plus an optional chartreuse dot. It must work in one colour, in dark mode and at 16 px. Keep texture only for large illustration.
- [I] The wordmark scales better than the icon. Consider a letter-based app icon from the "O" plus the loop.

## 10. What a static board cannot prove

- Whether real parents read "What else could be true?" as curiosity or as blame.
- Whether they spot that the Understand card is a guess, and whether they correct it.
- Behaviour under real stress or in the moment, Dynamic Type and VoiceOver order, small-screen layout, and motion.
- Dark mode, and the exact contrast of source tokens.
- Population appeal across cultures or caregiver types, trust around memory and privacy (absent from the board), retention, willingness to pay, and whether any family relationship actually changes.

## 11. A stronger alternative within your taste (fun but professional editorial)

**"Field notes on a wavelength."** Keep the ivory/aubergine serif, the dark-on-terracotta buttons and the two-figure attunement art. Change these:

1. **Hero:** run Notice → Understand → Rehearse → Try → Reflect as a four- or five-panel editorial spread. Each screen gets one display question; Rehearse shows the parent's actual words in a speech bubble.
2. **Understand screen:** three hand-set "maybe" cards ("Maybe: they were mid-play" / "Maybe: the rush felt scary" / "Maybe: something about the shoes"). Mark them as guesses with a small handwritten "you know them best", plus "None of these". This makes uncertainty part of the look instead of a disclaimer.
3. **Try screen:** two levers, "change the timing" and "change my pace", plus a "too much today → smaller step" link.
4. **Illustration:** two or three small vignettes of different caregivers (a dad at the door, a grandmother, the current mother), each mid-moment rather than serene. Use the textured style and drop the magnifier and the generic leaves.
5. **Brand:** one tagline only ("Wonder into practice"), a single-stroke wave-loop icon, and the violet either formalised or removed. Keep collage off the phone screens.

**Tradeoff:** it is busier to compose and less of a single poster image, but it shows the product's actual differentiator.

## 12. Tests with real parents

1. **Five-second test** on the board, then "What does this app do?" Code answers as understanding/self-change vs. tips vs. evaluation.
2. **Guess or fact (Understand).** Show the current phone 2 against the "maybe" version. Ask: "Is the app sure about this? Would you change it?" Measure whether people correct it and how they feel about the app.
3. **Show-up probe.** After the flow, ask: "What will *you* do differently?" Count answers that mention the parent's own pace or state vs. only a tactic aimed at the child.
4. **Perfect-parent / judgment check.** Show the hero illustration and ask: "How does this parent compare to you on a hard morning?" Look for shame cues.
5. **Self-recognition across caregivers.** Include fathers, grandparents, Spanish-dominant, low-income and neurodivergent parents. Ask "Is this for someone like you?" Report the subgroups separately; don't average them.
6. **Glance and stress proxy.** Run a timed one-handed task on a real small phone at large Dynamic Type after a distraction. Can they find the next step and "not now"?
7. **Comparison with a general assistant.** Run the same morning episode through a plain chatbot. Ask which one helped them understand their child, and which they would trust to remember.
8. **Icon recall.** After a 16/32 px home-screen exposure, can they pick out and describe Onda's icon?

## 13. How my earlier text-only hypotheses held up

| Earlier hypothesis | Verdict | Evidence |
|---|---|---|
| Rehearse is missing | **Confirmed** | [O] No rehearse screen. |
| Understand may read as one confident explanation | **Confirmed** | [O] A single declarative card. Phone 1 does separate feeling from facts, which is better than I expected. |
| Reflect may smuggle in a score | **Not confirmed** | [O] An open question with no metrics. |
| Low-capacity "smaller step" option | **Absent** | [O] One CTA only. |
| Privacy and "ask before remembering" | **Absent** | [O] Not shown anywhere. |
| Joy alongside difficulty | **Partly** | [O] The illustration is joyful; the flow covers a hard moment only. |
| Terracotta works as fill, not text, on ivory | **Confirmed** | [M] Fill 2.3; numerals about 3.3; buttons correctly use dark text at about 8:1. |
| Lilac and chartreuse too light on ivory | **Confirmed** | [M] About 1.5 each. |
| Softened palette lost the edge, generic editorial-wellness style | **Largely confirmed** | [I] Plus newly observed violet drift outside the swatches. |
| Icon may fail at small size or read as a generic loop | **Confirmed** | [O] Reads as a flower or atom; mush at 16 px. |

**Bottom line:** strong writing and a learnable loop inside a pleasant but trope-heavy shell. The Understand screen needs fixing before polish, then the flow (add Rehearse, give Reflect real weight, return to "I rushed"), then the brand (one tagline, a scalable icon, a disciplined palette). Every claim about appeal, stress usability, accessibility and efficacy still needs testing with real parents.
