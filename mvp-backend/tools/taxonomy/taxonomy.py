"""
Phase 1 taxonomy: 11 parents + their children, encoded verbatim from
docs/taxonomy-redesign.md (2026-05-12 co-founder list, doc-as-written).

This module is the single source of truth used by:
  - insert_taxonomy.py — POSTs parents + children to /cms/categories
  - remap_articles.py  — gives the LLM the full controlled vocabulary so
                         its suggestions stay inside the taxonomy

Stability rules:
  - IDs are kebab-case slugs. Never change a slug after it's in production.
  - Adding a new child is fine. Renaming a `name:` is fine. Renaming an `id:`
    breaks every article whose category points at it — treat IDs as opaque.
  - Top-level parents have parent_id=None; children carry their parent's id.

Tag vocabulary (Axis 2 from the doc) lives here too so the remap script
gives the LLM a closed set to draw from.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Category:
    id: str
    name: str
    emoji: str
    description: str
    parent_id: Optional[str] = None
    # Stable per-parent ordering hint for the UI. None = alphabetical.
    sort_key: Optional[int] = None


# Parents are inserted in this order. Children are inserted after all parents,
# ordered within each parent by declaration order.
TAXONOMY: list[tuple[Category, list[Category]]] = [
    (
        Category(
            id="pregnancy-babies",
            name="Pregnancy & Babies",
            emoji="🤰",
            description="Pregnancy through the first two years — the body, the gear, the basics.",
        ),
        [
            Category(id="pregnancy", name="Pregnancy", emoji="🤱", description="From conception through birth."),
            Category(id="postpartum", name="Postpartum", emoji="🌿", description="Recovery, pelvic floor, the fourth trimester."),
            Category(id="diapers-pullups", name="Diapers & pull-ups", emoji="👶", description="Disposables, cloth, and the transition out."),
            Category(id="formula", name="Formula", emoji="🍼", description="Choosing, mixing, troubleshooting."),
            Category(id="baby-food-delivery", name="Baby food & delivery", emoji="🥣", description="Solids, purees, and food-delivery services."),
            Category(id="strollers-carriers", name="Strollers & carriers", emoji="🛒", description="Picks for daily life and travel."),
            Category(id="daycare", name="Daycare", emoji="🏫", description="Choosing care for the under-3 set."),
        ],
    ),
    (
        Category(
            id="raising-kids",
            name="Raising Kids",
            emoji="🧒",
            description="Sleep, play, friendship, identity — the daily work of growing humans.",
        ),
        [
            Category(id="sleep-kids", name="Sleep for kids", emoji="😴", description="Routines, regressions, night wakings."),
            Category(id="sleep-machines-nightlights", name="Sleep machines & nightlights", emoji="🌙", description="Tools and picks."),
            Category(id="sel-trauma", name="SEL & trauma", emoji="💗", description="Social-emotional learning and trauma-aware parenting."),
            Category(id="peer-pressure", name="Peer pressure", emoji="👥", description="Navigating influence from friends, school, screens."),
            Category(id="bullying", name="Bullying", emoji="🛡️", description="Recognising, intervening, recovering."),
            Category(id="etiquette", name="Etiquette", emoji="🤝", description="Manners, respect, code-switching."),
            Category(id="raising-girls", name="Raising girls", emoji="👧", description="Identity, voice, body, agency."),
            Category(id="raising-boys", name="Raising boys", emoji="👦", description="Emotion, masculinity, accountability."),
            Category(id="books-by-age", name="Books by age", emoji="📚", description="Reading recs across childhood."),
            Category(id="toys", name="Toys", emoji="🧸", description="Open-ended play and what to skip."),
            Category(id="crafts", name="Crafts", emoji="✂️", description="Hands-on creative time."),
            Category(id="music", name="Music", emoji="🎵", description="Listening, making, learning."),
            Category(id="play-dates", name="Play dates", emoji="🎈", description="Hosting, joining, navigating other families."),
            Category(id="concerts-with-kids", name="Concerts with kids", emoji="🎤", description="Live music as a family."),
        ],
    ),
    (
        Category(
            id="school-activities",
            name="School & Activities",
            emoji="🎒",
            description="Education, enrichment, and the logistics that hold them together.",
        ),
        [
            Category(id="preschool", name="Preschool", emoji="🏫", description="Early-childhood programs."),
            Category(id="public-school", name="Public school", emoji="🏛️", description="Navigating the public system."),
            Category(id="private-school", name="Private school", emoji="🎓", description="Independent and religious options."),
            Category(id="tutors", name="Tutors", emoji="👩‍🏫", description="When, where, and what to ask for."),
            Category(id="clubs", name="Clubs", emoji="🤸", description="Interest-based group activities."),
            Category(id="after-school", name="After-school activities", emoji="⚽", description="Sports, arts, and the calendar reality."),
            Category(id="field-trips", name="Field trips", emoji="🚌", description="Day-trip and class-trip prep."),
            Category(id="camps", name="Camps", emoji="🏕️", description="Day and overnight."),
            Category(id="languages", name="Languages", emoji="🗣️", description="Bilingual/multilingual households and learners."),
            Category(id="schedules-admin", name="Schedules & admin", emoji="🗓️", description="The paperwork, forms, and signups behind it all."),
        ],
    ),
    (
        Category(
            id="family-life",
            name="Family Life & Relationships",
            emoji="❤️",
            description="The web of relationships — partners, kids, exes, money, life events.",
        ),
        [
            Category(id="first-time-parents", name="First-time parents", emoji="🌱", description="Navigating the first kid."),
            Category(id="single-parent", name="Single parent", emoji="🌟", description="Solo parenting realities."),
            Category(id="working-parent", name="Working parenthood", emoji="💼", description="Career + parenting integration."),
            Category(id="stay-at-home", name="Stay-at-home", emoji="🏡", description="Identity and rhythm of full-time at home."),
            Category(id="marriage-date-nights", name="Marriage & date nights", emoji="💑", description="Sustaining the partnership."),
            Category(id="sex-life", name="Sex life", emoji="💞", description="Intimacy after kids."),
            Category(id="divorce-coparenting", name="Divorce / separation / co-parenting", emoji="🤲", description="Separation and shared custody."),
            Category(id="siblings", name="Siblings", emoji="🧑‍🤝‍🧑", description="Rivalry, bond, birth order."),
            Category(id="friendships", name="Friendships", emoji="💛", description="Adult friendships in the parenting years."),
            Category(id="abuse-cps", name="Abuse, neglect & CPS", emoji="⚠️", description="Recognising abuse; the CPS system; safety planning."),
            Category(id="estate-planning", name="Estate planning", emoji="📜", description="Wills, guardianship, what-if planning."),
            Category(id="finances-with-kids", name="Finances with kids", emoji="💰", description="Budgeting and money lessons across ages."),
        ],
    ),
    (
        Category(
            id="health-kids",
            name="Health: Kids",
            emoji="🩺",
            description="Pediatric care across the spectrum — mainstream and integrative.",
        ),
        [
            Category(id="pediatrician", name="Pediatrician", emoji="👩‍⚕️", description="Visits, vaccines, and choosing a doc."),
            Category(id="dentist-kids", name="Dentist", emoji="🦷", description="First visit through teen."),
            Category(id="orthodontist", name="Orthodontist", emoji="😬", description="Braces, aligners, palate expanders."),
            Category(id="specialty-medical", name="Specialty medical", emoji="🏥", description="Specialists when needed."),
            Category(id="integrative-eastern", name="Functional / integrative / Eastern", emoji="🌿", description="Complementary approaches."),
            Category(id="meds-kids", name="Meds for kids", emoji="💊", description="Prescriptions and OTC for pediatric care."),
            Category(id="vaccines", name="Vaccines", emoji="💉", description="Schedule, timing, common questions."),
            Category(id="sickness-kids", name="Sickness", emoji="🤒", description="Common illnesses and when to call the doctor."),
        ],
    ),
    (
        Category(
            id="health-parents",
            name="Health: Parents (Wellness)",
            emoji="🧘",
            description="Adult wellness across mind, body, midlife.",
        ),
        [
            Category(id="mental-health", name="Mental health", emoji="🧠", description="Therapy, meds, daily mental upkeep."),
            Category(id="anxiety", name="Anxiety", emoji="🌊", description="Living with and managing anxiety."),
            Category(id="perimenopause", name="Perimenopause", emoji="🔥", description="Symptoms, treatment, partnership."),
            Category(id="sleep-parents", name="Sleep for parents", emoji="🛌", description="Sleep hygiene and recovery."),
            Category(id="exercise-longevity", name="Exercise for longevity", emoji="💪", description="Strength, mobility, cardio for the long haul."),
            Category(id="hydration", name="Hydration", emoji="💧", description="What and how much."),
            Category(id="hair", name="Hair", emoji="💇", description="Postpartum, midlife, and the in-between."),
            Category(id="plastic-surgery", name="Plastic surgery & refresh", emoji="✨", description="Procedures, decisions, recovery."),
            Category(id="drugs-parents", name="Drugs (Rx + recreational)", emoji="🧪", description="The full landscape — needs legal review before content goes live."),
            Category(id="parental-longevity", name="Parental longevity", emoji="⏳", description="Living long and well for our kids."),
            Category(id="midlife-crisis", name="Mid-life crisis", emoji="🌀", description="Naming and navigating it."),
            Category(id="sickness-parents", name="Sickness", emoji="🤧", description="When the grown-ups get sick."),
        ],
    ),
    (
        Category(
            id="food-nutrition",
            name="Food & Nutrition",
            emoji="🍎",
            description="What's on the table, in the lunchbox, and in the cart.",
        ),
        [
            Category(id="recipes", name="Recipes", emoji="🍳", description="Family-tested recipes."),
            Category(id="breakfast", name="Breakfast", emoji="🥞", description="Morning fuel."),
            Category(id="lunchboxes", name="Lunchboxes", emoji="🥪", description="School lunches that get eaten."),
            Category(id="snacks", name="Snacks", emoji="🍿", description="Between-meal options."),
            Category(id="dinners", name="Dinners", emoji="🍽️", description="Weeknight rescue plates."),
            Category(id="meal-delivery", name="Meal delivery", emoji="📦", description="Kits, prepared meals, and what's worth it."),
        ],
    ),
    (
        Category(
            id="care-village",
            name="Care & Village",
            emoji="🤝",
            description="The humans who help — and how to be one yourself.",
        ),
        [
            Category(id="nannies", name="Nannies", emoji="🧑‍🍼", description="Live-in, live-out, finding and keeping."),
            Category(id="babysitters", name="Babysitters", emoji="👶", description="Occasional care and date nights."),
            Category(id="village-community", name="Village & community", emoji="🏘️", description="Building one when you weren't born into one."),
            Category(id="advocacy", name="Advocacy", emoji="📢", description="Speaking up for kids and families."),
            Category(id="philanthropy", name="Philanthropy", emoji="🎁", description="Giving with kids, raising givers."),
        ],
    ),
    (
        Category(
            id="home-style-products",
            name="Home, Style & Products",
            emoji="🏠",
            description="The stuff of family life — gear, clothes, tech, and the homes that hold it all.",
        ),
        [
            Category(id="cars", name="Cars", emoji="🚗", description="Kid-safe and planet-friendly choices."),
            Category(id="cleaning", name="Cleaning", emoji="🧽", description="Products and rhythms."),
            Category(id="furniture", name="Furniture", emoji="🛋️", description="Kid-friendly that adults still like."),
            Category(id="home-decor", name="Home decor", emoji="🖼️", description="Family-friendly aesthetic."),
            Category(id="tech", name="Tech", emoji="💻", description="Devices, screen agreements, useful tools."),
            Category(id="kids-clothes", name="Kids' clothes", emoji="👕", description="Picks, sizing, durability."),
            Category(id="kids-shoes", name="Kids' shoes", emoji="👟", description="Growing feet and what they need."),
            Category(id="upcycled-clothes", name="Upcycled clothes", emoji="♻️", description="Pre-loved and circular."),
            Category(id="parents-sleepwear", name="Parents' sleepwear", emoji="🩱", description="What we wear to bed when there are humans."),
            Category(id="undergarments", name="Undergarments (pre/post kids)", emoji="🩲", description="What fits across the journey."),
            Category(id="fashion", name="Fashion", emoji="👗", description="Adult style, parent edition."),
            Category(id="personal-care", name="Personal care", emoji="🧴", description="Face and body."),
        ],
    ),
    (
        Category(
            id="out-in-world",
            name="Out in the World",
            emoji="🌍",
            description="Family life beyond the front door — travel, culture, civic life.",
        ),
        [
            Category(id="travel", name="Travel", emoji="✈️", description="With kids, near and far."),
            Category(id="outings", name="Outings", emoji="🚶", description="Day trips and afternoon adventures."),
            Category(id="museums", name="Museums", emoji="🏛️", description="Family-friendly cultural visits."),
            Category(id="nature", name="Nature", emoji="🌲", description="Time outdoors, big and small."),
            Category(id="movies", name="Movies", emoji="🎬", description="What to watch as a family."),
            Category(id="entertaining", name="Entertaining", emoji="🎉", description="Hosting with kids in the mix."),
            Category(id="culture", name="Culture", emoji="🎭", description="Theatre, art, ideas worth exposing kids to."),
            Category(id="politics", name="Politics", emoji="🗳️", description="Raising civic awareness without doom."),
            Category(id="planet-us", name="The planet and us", emoji="🌎", description="Climate-aware living with kids."),
            Category(id="outdoor-gear", name="Outdoor gear", emoji="🚲", description="Bikes, scooters, hiking gear."),
        ],
    ),
    (
        Category(
            id="inner-life",
            name="Inner Life",
            emoji="🕊️",
            description="The interior of being a parent — practice, presence, and meaning.",
        ),
        [
            Category(id="mindfulness", name="Mindfulness & being present", emoji="🧘‍♀️", description="Practices for actually being here."),
            Category(id="spirituality", name="Spirituality", emoji="✨", description="The woo-woo lane — open and inclusive."),
            Category(id="books-parents", name="Books for parents", emoji="📖", description="Reading that grows the grown-up."),
        ],
    ),
]


# Axis 2 — orthogonal tags (closed set for the LLM remap).
TAG_VOCABULARY = {
    "age_band": ["newborn", "infant", "toddler", "preschool", "elementary", "tween", "teen"],
    "stage_identity": [
        "first-time-parent", "single-parent", "working-parent", "stay-at-home",
        "postpartum", "coparenting",
    ],
    "voice_inspiration": [
        "inspired-by-becky", "inspired-by-huberman", "inspired-by-amen",
        "inspired-by-hyman", "inspired-by-mate", "inspired-by-spiritual",
    ],
    "concern": ["planet-friendly", "budget-friendly", "safety-critical"],
    "format": [
        "recipe", "product-pick", "link-roundup", "podcast-pick",
        "script", "routine", "deep-dive",
    ],
}


def all_parents() -> list[Category]:
    return [parent for parent, _ in TAXONOMY]


def all_children() -> list[Category]:
    out: list[Category] = []
    for parent, children in TAXONOMY:
        for child in children:
            # Set the parent_id at access time so the source-of-truth dict
            # doesn't have to repeat the parent slug on every line.
            child.parent_id = parent.id
            out.append(child)
    return out


def all_categories() -> list[Category]:
    """Parents first, then children (so a re-inserter sees a valid graph)."""
    out: list[Category] = []
    out.extend(all_parents())
    out.extend(all_children())
    return out


def all_top_level_ids() -> list[str]:
    return [p.id for p in all_parents()]


def all_child_ids() -> list[str]:
    return [c.id for c in all_children()]


def flat_tag_list() -> list[str]:
    out: list[str] = []
    for v in TAG_VOCABULARY.values():
        out.extend(v)
    return out


if __name__ == "__main__":
    cats = all_categories()
    parents = all_parents()
    children = all_children()
    print(f"parents: {len(parents)}")
    print(f"children: {len(children)}")
    print(f"total:   {len(cats)}")
    print(f"tags:    {len(flat_tag_list())}")
    for parent, kids in TAXONOMY:
        print(f"  {parent.id:25} → {len(kids):2} children")
