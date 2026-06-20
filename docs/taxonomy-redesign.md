# Content Taxonomy Redesign — Categories, Tags, Editorial

> **Status (2026-06-19):** Phase 0 (schema + iOS `parent_id`/`topLevelCategories` filter) **and** Phase 1 (taxonomy population) are **done** — `data/categories.parquet` now holds **11 top-level + 99 child categories**, with articles + community posts remapped. Phase 2 (editorial pipeline / "inspired-by" content) and Phase 3 (two-level hierarchical browse UX — iOS still uses the `topLevelCategories` stopgap) are **not started**. This doc remains the live spec for those remaining phases.

**Date:** 2026-05-12
**Driver:** Co-founder ask for a richer set of content categories (too many for flat browsing → hierarchical). Plus a tagging system. Plus seeded editorial content inspired by Becky Kennedy, Mark Hyman, Daniel Amen, Gabor Maté, Andrew Huberman, and spiritual principles.

## Context

Today: **10 flat categories**, 45 articles, 20 community posts. Recon found two useful surprises:
- **`articles.tags TEXT[]` already exists** in the DuckDB schema, the API encodes/decodes it, and the **CMS form already collects tags** (`ArticleForm.tsx:163-178`, comma-separated). It's just empty in data and unrendered on iOS.
- **`articles.category` is a free string with no FK** — adding a `categories.parent_id` is purely additive; the existing 45 articles keep working untouched until they're re-mapped.

So "hierarchy + tags" is roughly half-built infrastructure and half-greenfield UX, not a from-scratch rewrite.

## Decisions (from 2026-05-12 plan-mode questions)

| Question | Decision |
|---|---|
| Where does the taxonomy come from? | Miguel will paste the canonical list from co-founder (pending). |
| What happens to the 45 existing articles? | **Re-map** to the new taxonomy with an LLM-assisted suggestion + CMS review step. No archive. |
| Content sourcing from the named voices | **Original-inspired editorial.** We write the articles; attribution + outbound links to the source authors. No licensed text, no AI-summarized copies. |

## Phased plan

### Phase 0 — list-independent infrastructure (can start immediately, in parallel with sourcing the list)

1. **Schema migration** (via `app/migrations.py`): add `categories.parent_id TEXT NULL` (self-FK by `id`). Null = top-level. Forward-only; existing 10 categories stay valid as roots.
2. **Backend API**: `/content/categories` returns the existing shape plus `parent_id`. New `/content/articles?tag=<slug>` filter. CMS endpoints (`/cms/categories`) accept `parent_id` on POST/PUT.
3. **CMS editor changes** (`mvp-backend/cms/`):
   - `CategoryForm.tsx`: add a `parent_id` dropdown sourced from existing categories (top-level only — no 3+-level deep).
   - `ArticleForm.tsx`: keep the comma-separated tags field but render a chip-style preview; convert to chip-input is a v2 polish.
   - **Send `X-Admin-Token`** (existing roadmap item — required after the recent backend lock).
4. **iOS tag rendering + filter**: `APIArticle.tags` is already on the wire. Add a chip row on `ArticleDetailView` and a tag filter pill on `LibraryView`/`CategoryDetailView`.

Files most affected (representative — pattern repeats):
- Backend: `mvp-backend/app/duckdb_storage.py`, `mvp-backend/app/migrations.py`, `mvp-backend/app/server.py` (CMS endpoints + new tag-filter param), `mvp-backend/app/content.py`.
- CMS: `mvp-backend/cms/src/pages/CategoryEditor.tsx`, `mvp-backend/cms/src/components/editors/CategoryForm.tsx`, `mvp-backend/cms/src/api/index.ts`.
- iOS: `mvp/MVP/ContentService.swift`, `mvp/MVP/ContentViewModel.swift`, `mvp/MVP/LibraryView.swift`, `mvp/MVP/ArticleDetailView.swift`, `mvp/MVP/ContentCardViews.swift`.

### Phase 1 — taxonomy population (blocked on Miguel's list)

Once we have the canonical list:
1. Generate a single ordered SQL migration that inserts the new categories with their hierarchy.
2. **LLM-assisted re-mapping** of the 45 existing articles: a one-shot script that proposes `(new_category, suggested_tags)` per article and writes a `category_mapping_proposals` table; the CMS gains a `/cms/migration` page where the editor confirms each.
3. Deprecate the old 10 category IDs by renaming/relinking, not deleting (so any external URLs keep resolving).

### Phase 2 — editorial pipeline (after taxonomy is live)

1. **Authorial voice doc** — short style guide pinning tone, length, attribution format, what counts as fair-use vs. paraphrase.
2. **Per-influence template** — a CMS "starter" with the right framing for Becky / Hyman / Amen / Maté / Huberman / spiritual angle. New optional article fields: `inspired_by_author`, `inspired_by_source_url`, `attribution_text`.
3. **Backfill set** — initial 4-6 articles per new category, drafted in the CMS, reviewed before publish.
4. **Legal posture:** original prose, ≤ ~50-word block quotes treated as fair use with attribution and link, no podcast transcripts or book excerpts.

### Phase 3 — iOS UX for hierarchical browse

1. **Two-level browse:** parent category → subcategory grid → article list. Reuse the existing `CategoryDetailView` for the leaf level; add a `ParentCategoryView` upstream.
2. **Tag chips** on article cards + a tag-filter pill on category-detail.
3. **Search** across category + tag + title + body (backend `/content/search` already exists for title; extend it).
4. **"Inspired by X" shelves** on Home — a horizontal scroller per named voice, surfacing matching articles.

## Verification

- All schema changes go through `app/migrations.py` and show up in `schema_migrations` on next boot.
- Old article URLs (`/content/articles/{id}`) keep resolving — no ID changes during the re-map.
- iOS: open `LibraryView`, drill into a parent category, confirm the subcategory grid appears and a tag filter narrows the list.
- CMS: log into `/cms`, edit a category to give it a parent, confirm the iOS list re-groups.
- Migration is idempotent — running it twice produces no duplicate rows (UNIQUE constraints + `INSERT OR IGNORE`).

## Proposed taxonomy (from the 2026-05-12 co-founder list — 110 items normalized)

**Product scope:** children **ages 0–18**. The app covers the full arc — pregnancy & infancy through teens — so parents don't graduate out and we can carry one user from their first kid through their last.

The raw list mixes **topics, stages, audiences, and formats**. Treating all of them as categories produces a flat unscannable menu. The proposal splits them into three orthogonal axes:

### Axis 1 — 11 parent categories (topical, what the article is *about*)

Items that span multiple ages (car seats run to ~12, sleep machines through teens, wagons through grade-school) live in their broadest natural home rather than being duplicated. Diaper/formula/baby-food items live cleanly under Pregnancy & Babies since they don't extend past ~2.

| Parent | Children |
|---|---|
| **Pregnancy & Babies** | Pregnancy · Postpartum (incl. pelvic floor) · Diapers & pull-ups · Formula · Baby food & delivery · Strollers & carriers · Daycare |
| **Raising Kids** | Sleep for kids · Sleep machines & nightlights · SEL & trauma · Peer pressure · Bullying · Etiquette · Raising girls · Raising boys · Books by age · Toys · Crafts · Music · Play dates · Concerts with kids |
| **School & Activities** | Preschool · Public school · Private school · Tutors · Clubs · After-school activities · Field trips · Camps · Languages · Schedules & admin |
| **Family Life & Relationships** | First-time parents · Single parent · Working parenthood · Stay-at-home · Marriage & date nights · Sex life · Divorce / separation / co-parenting · Siblings · Friendships · Abuse, neglect & CPS · Estate planning · Finances with kids |
| **Health: Kids** | Pediatrician · Dentist · Orthodontist · Specialty medical · Functional / integrative / Eastern · Meds for kids · Vaccines · Sickness |
| **Health: Parents (Wellness)** | Mental health · Anxiety · Perimenopause · Sleep for parents · Exercise for longevity · Hydration · Hair · Plastic surgery & "refresh" · Drugs (Rx + recreational) · Parental longevity · Mid-life crisis · Sickness |
| **Food & Nutrition** | Recipes · Breakfast · Lunchboxes · Snacks · Dinners · Meal delivery |
| **Care & Village** | Nannies (live-in / live-out) · Babysitters · Village & community · Advocacy · Philanthropy |
| **Home, Style & Products** | Cars (kid-safe & planet-friendly) · Cleaning · Furniture (kid-friendly) · Home decor (kid-friendly) · Tech · Kids' clothes · Kids' shoes · Upcycled clothes · Parents' sleepwear · Undergarments (pre/post kids) · Fashion · Personal care (face & body) |
| **Out in the World** | Travel · Outings · Museums · Nature · Movies · Entertaining · Culture · Politics · The planet and us · Outdoor gear (bikes, scooters, hiking) |
| **Inner Life** | Mindfulness & being present · Spirituality (the "woo-woo" lane) · Books for parents |

### Axis 2 — orthogonal tags (cross-cutting, an article can have many)

Tags are **M:N** with articles (the existing `articles.tags TEXT[]` column). They cross categories cleanly without bloating the menu.

- **By age band**: `newborn` (0-1) · `infant` (1-2) · `toddler` (2-3) · `preschool` (3-5) · `elementary` (6-10) · `tween` (10-12) · `teen` (13-18)
- **By stage / identity**: `first-time-parent`, `single-parent`, `working-parent`, `stay-at-home`, `postpartum`, `coparenting`
- **By voice / inspiration**: `inspired-by-becky`, `inspired-by-huberman`, `inspired-by-amen`, `inspired-by-hyman`, `inspired-by-mate`, `inspired-by-spiritual`
- **By concern**: `planet-friendly`, `budget-friendly`, `safety-critical`
- **By format**: `recipe`, `product-pick`, `link-roundup`, `podcast-pick`, `script`, `routine`, `deep-dive`

### Axis 3 — "Recommended reading" hub (not a parent category)

`Best blogs`, `Best email lists`, `Best social content`, and `Podcasts` are *resource lists*, not editorial content. Treat them as one CMS-curated hub page surfaced from Home, populated via the `link-roundup` and `podcast-pick` format tags rather than as top-level categories. Each podcast pick still gets the relevant topical category (e.g. a Huberman sleep episode → `Health: Parents / Sleep for parents` + `podcast-pick` + `inspired-by-huberman`).

### Editorial flags from the raw list (need your call)

1. **"Vaccines — yes to all. Always."** A category is fine; this is a strong editorial stance that should live in the article voice, not the category label. I'll keep the topic neutral as `Vaccines` and let the articles take the position.
2. **"Drugs for kiddos and adults"** is currently ambiguous (Rx? recreational? both?). Recommend splitting in CMS into `Meds for kids` (under Health: Kids) and `Drugs` (under Health: Parents, covering Rx + cannabis/recreational landscape). Flag for legal review before any content goes live — same posture as the kid-agent stack.
3. **"Pods"** is ambiguous — childcare pods (covid-era cohort), mom-friend pods, or podcasts? Assumed childcare/community pods under "Care & Village." Confirm.
4. **"Admin shit"** rolled into `Schedules & admin` under School & Activities. Renamed for CMS but the underlying topic stands.
5. **"The mindfuck of parenting girls v boys"** split into two sibling sub-categories: `Raising girls` + `Raising boys`. The "mindfuck" framing becomes the voice of the articles, not the category name.
6. **"Marriage. Laugh. Go on Dates and do it."** sub-category named `Marriage & date nights`. Same — voice stays.
7. **"Hydration"** appeared twice (parents-wellness and food-nutrition). Single home under Health: Parents; can be tagged from a recipe.
8. **"Sickness"** also appears in both health buckets; kept under each since pediatric sickness ≠ adult sickness.
9. **Duplicates collapsed:** Postpartum (mentioned 3x), Sleep (kids + parents kept separate), Field trips (lives under School, not Out in the World).
10. **Two items dropped from the category list (kept as tags):** the named-author "inspired by" labels (these are tags, not categories — every article is inspired by *someone*).

### Why this shape vs. flat

- **2-level deep, not 3.** Nielsen Norman card-sort research and Lifekit/Headspace IA both top out at 2 — past that, browse abandonment spikes and users default to search. The list maps comfortably into 2 levels.
- **Tags carry the cross-cuts.** Stage ("single parent"), age, voice, and format are cross-cutting realities that explode any categorical taxonomy. Putting them in tags lets a single article surface in multiple natural contexts without duplication.
- **Audiences as parents, not children.** "Health: Kids" vs "Health: Parents" reads cleanly because audience drives the whole article's tone; no need for an "audience" tag dimension.

## Open inputs (now reduced)

- **Sign-off on the 11 parents** above (or edits — happy to merge / split / rename).
- **The editorial flags** — especially Pods, Vaccines voice, Drugs scope.
- Whether to start Phase 0 (the list-independent schema + iOS tag rendering) in parallel while we shape this, or wait for full sign-off.

## What I can do right now without the list

Phase 0 — entirely list-independent. The schema column, the API field, the CMS picker, the iOS tag chip rendering: none of it cares what the categories ARE, only that hierarchy + tagging exist. Building Phase 0 in parallel saves a sprint.
