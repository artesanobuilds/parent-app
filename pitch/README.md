# pitch/

The MVP investor deck and everything behind it.

| File | What it is |
| --- | --- |
| `MVP-Investor-Deck.pptx` | The deliverable. 16 slides, with two versions of slide 15 (the CTO bio) to pick between: keep one, delete the other. Open in Keynote or import to Google Slides. |
| `build_deck.py` | Generates the pptx. Design tokens at the top were measured out of Heather's original slide, so this sits on her exact grid. Includes a layout audit that fails loudly on overflow. |
| `narrative.md` | The argument: the strategy kernel, the refusals, and the slide-by-slide script with speaker notes. |
| `critics.md` | Fadell, Jobs and Horowitz on the first draft, and what changed because of it. |
| `evidence.md` | Every factual claim mapped to its source. Read before a meeting. |
| `midjourney-prompts.md` | Image prompts for slide 02, in the beta-v1 visual language. |
| `assets/` | Generated imagery. Product screenshots live in `parent-dashboard/public/docs-assets/` if a visual slide is ever added back. |

## Rebuilding

`python-pptx` is not a project dependency. Build in a throwaway venv:

```
uv venv /tmp/deckvenv
uv pip install --python /tmp/deckvenv/bin/python python-pptx
/tmp/deckvenv/bin/python pitch/build_deck.py
```

The build prints a layout audit. `audit: 0 layout problem(s)` means nothing runs into the footer
band or off the right margin. Anything else names the slide and the offending text.

## Checking it visually

Text heights are estimated, not measured, so always look at the result after changing copy:

```
soffice --headless --convert-to pdf --outdir /tmp/render pitch/MVP-Investor-Deck.pptx
pdftoppm -png -r 50 /tmp/render/MVP-Investor-Deck.pdf /tmp/render/s
```

## Design system

Cream `#F5F0EA` ground, `#FCFBF8` cards, ink `#282019`, body `#6E6455`, muted `#9A9080`, teal
`#1B7498`. Fraunces for display, Inter for body, JetBrains Mono for labels. This is the app's
Hearth beta-v1 palette, which is also what Heather's deck was already built on.

Slide 02 is the only dark slide. Keep it that way; a second one costs the first its impact.
