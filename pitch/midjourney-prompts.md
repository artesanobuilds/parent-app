# Midjourney prompts — slide 02, the thesis

Slide 02 is the one slide that should stop a partner scrolling. Right now it carries type on the
ink ground. An image would earn its place there, provided it stays inside the visual language the
rest of the product already speaks.

These prompts come from the converged parent-app recipe (`memory/reference_mj_prompt_template_parentapp.md`),
tuned to the beta-v1 redesign palette: warm cream `#F5F0EA`, ink `#282019`, teal `#1B7498`.

## The rules that do not change

Keep the lighting, film stock, negative space and the full `--no` list intact across every
generation. That consistency is what makes ten unrelated images read as one set. Tune only the
subject and the environment.

No faces. No sunsets or silhouettes. No visible text or lettering, which reads as designed rather
than found. And no hand-on-shoulder parenting cliché.

## Primary — the object that carries the idea

The thesis is that something powerful arrived for professionals and has not reached the home. The
image should be a domestic surface at the end of a long day, holding the evidence of an
unmanaged operations job. The viewer should feel the load without being shown a person carrying it.

```
/imagine: editorial photograph, a kitchen table at the end of the day, a stack of school
paperwork and a crumpled activity flyer beside a cooling mug, one phone face-down at the
edge of the frame, late afternoon north-window light, warm hardwood and cream linen, soft
shadows, shot on 35mm film grain, kodak portra 400, slightly desaturated, generous negative
space on the left third, magazine spread aesthetic --ar 16:9 --style raw --v 6
--no AI-glossy, plastic skin, oversaturation, perfect-teeth, sunset cliche, faces, people,
hands, text, lettering, brand logos, clutter, mess
```

Note the `generous negative space on the left third`: the slide sets its title on the left, so the
image needs a quiet area to sit under. If the generation fills the frame edge to edge, reroll
rather than cropping.

## Fallback — the calm after

If the primary reads as stressful rather than quiet, the same table after the job is handled. This
is the version to use if the slide ends up feeling heavy in context.

```
/imagine: editorial photograph, a cleared wooden kitchen table in early evening, a single
calendar page and a pen set square to the edge, a small glass of water, everything in its
place, late afternoon north-window light, warm hardwood, soft shadows, shot on 35mm film
grain, kodak portra 400, slightly desaturated, generous negative space, magazine spread
aesthetic --ar 16:9 --style raw --v 6
--no AI-glossy, plastic skin, oversaturation, perfect-teeth, sunset cliche, faces, people,
hands, text, lettering, brand logos
```

## If you want a full-bleed variant

For a version where the image runs the whole slide with the title reversed out over it, generate
at `--ar 16:9` and add `dark warm shadow across the upper third for type overlay` to the subject
line. Ask before using this one: the deck currently has exactly one dark slide, and two would
dilute the effect.

## Wiring it in

Drop the chosen file at `pitch/assets/thesis.png`, then in `build_deck.py`, slide 02, add the
picture before the cards and shift the card row down. The layout audit will tell you immediately
if it does not fit.

Generate one, look at it on the slide, then decide. Do not generate all three and pick on a
contact sheet: these read differently in place than they do side by side.
