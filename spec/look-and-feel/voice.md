# Voice — Hearth

How Hearth speaks. Same hand on the shoulder, every screen.

The voice is **warm, concrete, second-person, present-tense.** It writes the way a friend with credentials would talk — never a brand, never a chatbot, never the kind of "we" that means a marketing team. It is functional in chrome, editorial in long-form, sober in crisis. It earns trust by being specific.

## Register matrix

| Surface | Register | Case | Tense | Emoji |
|---|---|---|---|---|
| Chrome (nav labels, buttons, form labels, microcopy) | functional | lowercase | active present | never |
| Body copy (cards, descriptions, empty states) | warm functional | sentence case | active present | never |
| Long-form headlines (article titles, section headers in articles) | editorial | Title Case Headlines | flexible | never |
| Long-form body | editorial, conversational | sentence case | active present (occasional past for narrative) | never |
| Kid-agent (sober variant) | quiet, respectful | sentence case | active present | never |
| Crisis surface | sober, declarative | sentence case | active present | never; no `!` |
| Errors | warm + specific | sentence case | active present | never |
| Community posts (user-generated; not our voice but moderated under it) | user's own | as-typed | as-typed | as-typed, within moderation |

## Tense

Active present everywhere. "You're saving this article" not "this article will be saved." Past tense only inside long-form narrative where someone is telling a story. Future tense is almost always a sign we're hedging — rewrite.

## Pronouns

- **You** addresses the parent. Always.
- **We** is rare. Use only when Hearth itself is taking an action on the parent's behalf ("we're loading your library"). Never the marketing "we" ("we believe parenting is...").
- **They / them** for the kid by default when the kid's gender isn't established. Use the kid's name once it's known.
- Never "users." Never "parents will." Always "you."

## Case rules

- **lowercase** in functional UI: nav labels, button text, form labels, chip labels, tab titles, helper text. Lowercase reads warmer at small sizes and matches Wonder Valley / Rose LA convention.
- **Sentence case** in body copy and cards. Standard prose capitalization.
- **Title Case Headlines** only in long-form articles. Real magazine titles. Capitalize principal words.
- **UPPERCASE** only for `type/label` token instances — nav-section labels, tag chips, the wordmark. Letterspacing `+6%`.

## Headline rhythm (long-form)

- Top headline: 4–9 words. Concrete subject + concrete verb.
- Subhead: 8–14 words. Adds one piece of information the headline implies.
- Section headers: 2–5 words. Functional, scannable.
- No clickbait. No "you won't believe." No questions as headlines unless the article literally answers that question in the first paragraph.

## Body rhythm

- One idea per sentence; short sentences earn the long one.
- Concrete nouns and verbs. Cut adverbs.
- Numbers as numerals (`3 weeks`, not `three weeks`) unless beginning a sentence.
- Em dash for asides — like this — not parens unless deeply nested.
- Oxford comma. Always.

## Emoji rules

- **Never in chrome.** Not in nav, not in buttons, not in form labels, not in error messages, not in toasts.
- **Never in long-form articles.** Not in headlines, not in body.
- **Acceptable in category tiles only as a temporary stand-in during dev** while photography is being generated. Replaced before any production cut.
- **Never in crisis-surface copy.** Ever.
- **Community posts** keep the user's own emoji within moderation limits; we don't strip them.

## Errors — 5 good, 5 bad

Errors are warm, specific, present-tense, and tell the parent what to do next. They never blame the parent and never use exclamation marks.

**Good.**

| Context | Copy |
|---|---|
| Article fetch failed | `couldn't load articles. pull down to retry.` |
| Login wrong password | `that password doesn't match. try again, or reset it below.` |
| Photo upload too large | `photo is over 10mb. try a smaller one or take a new shot.` |
| Network offline | `you're offline. saved articles still work; the rest is waiting on a connection.` |
| Form field missing | `your kid's age helps us pick the right articles. add it to keep going.` |

**Bad.**

| Why it's bad | Copy |
|---|---|
| Tech-speak, no next step | `Error 500: Internal Server Error` |
| Blames the parent | `Invalid input! Please try again.` |
| Cute when it shouldn't be | `oops! something went sideways 😅 our gremlins are on it!` |
| Brand "we" + corporate | `We're sorry, but we are unable to process your request at this time.` |
| Vague + alarming | `Something went wrong. Please contact support.` |

The pattern in every good error: **what happened (specific) — what you can do next (specific) — no shame, no exclamation, no emoji.**

## Crisis-surface tone

This register applies on the kid-agent crisis lock, any safety lock, and the resources screen reached from either.

- Sober. Declarative. No metaphor.
- Sentence case. No Title Case. No lowercase functional UI shortcuts that read as casual.
- No exclamation marks. No "oops." No "we." No emoji.
- No "we're here for you" warmth-by-template. The design (`bg/sober`, type-only, generous whitespace) carries the warmth; the copy carries the information.
- Lead with the action the parent or kid can take. Then the number. Then the context. Never the reverse.
- Examples:
  - `if you or your kid needs to talk to someone right now, call or text 988. it's free and open 24/7.`
  - `this conversation is paused. a real person can help right now: 988 (call or text).`
- Never:
  - `you've got this!` on a crisis screen
  - any emoji
  - any animation beyond a single fade-in at `motion/fast`
  - photography of any kind

## Microcopy patterns

| Pattern | Example |
|---|---|
| Empty state | `nothing saved yet. tap the bookmark on any article to start a library.` |
| Loading | `loading your library…` (use `…` not `...`) |
| Confirm destructive | `delete this post? this can't be undone.` / button: `delete` |
| Success toast | `saved.` (one word, lowercase, no exclamation) |
| Skeleton placeholder | no copy — visual only |
| Form helper | `optional. helps us match articles to your kid's stage.` |
| Onboarding nudge | `one more step — your kid's first name.` |

## Word list — prefer / avoid

| Prefer | Avoid |
|---|---|
| you, your | the user, users, parents |
| your kid | your child (acceptable; "kid" reads warmer) |
| right now | currently, at this time |
| open | launch (unless literally launching) |
| save | bookmark (acceptable both, prefer save in chrome) |
| can't | cannot |
| we're loading | please wait |
| try again | retry |
| article | content piece, asset |
| library | saved items, collection |
| `—` em dash | `(parenthetical)` for short asides |

## Tokens used

```
type/display-xl
type/display-lg
type/display-md
type/title-lg
type/title-md
type/body-lg
type/body-md
type/body-sm
type/label
type/caption-mono
ink/primary
ink/secondary
ink/muted
bg/canvas
bg/sober
```

(Voice maps to type tokens; the type tokens enforce the case/weight rules via component specs.)

## Rules

- Lowercase functional UI; sentence-case body; Title Case Headlines in long-form only.
- Second person to the parent; never "users," never marketing "we."
- Active present. Cut future tense unless it's literally about the future.
- Errors are specific + actionable + shameless; no exclamation marks.
- No emoji in chrome, long-form, or any crisis-adjacent surface.
- Crisis copy is sober — no metaphor, no warmth-by-template, no `!`.
- One idea per sentence; short sentences earn the long one.
- Oxford comma; em dash over parens for short asides.
- Numerals for numbers; `…` not `...`.
- If a sentence could appear on any parenting brand's site tomorrow, rewrite it.

## Render check

The implementation must match these compositions.

1. **Onboarding step 2 — kid name input.** Label `your kid's first name` (lowercase), helper `we'll use this to personalize article picks.` (sentence case), primary button `continue` (lowercase). No emoji. `bg/canvas`.
2. **Article hero — long-form.** Headline `The Year We Stopped Negotiating Bedtime` (Title Case), byline `by hearth editorial · 6 min read` (`type/caption-mono`), body opens in sentence case.
3. **Error state — articles failed to load.** Copy `couldn't load articles. pull down to retry.` on `bg/canvas`, `ink/secondary`, no icon larger than 16pt, no exclamation.
4. **Kid-agent crisis lock.** Headline `this conversation is paused.` (sentence case, period), body `a real person can help right now: 988 (call or text).`, `bg/sober`, type-only, no photography, no emoji.
5. **Toast — saved.** Single word `saved.` on a `bg/elevated` chip, `ink/primary`, `motion/fast` fade-in.

---

status: ✅ active
owner: Miguel
last_updated: 2026-05-31
