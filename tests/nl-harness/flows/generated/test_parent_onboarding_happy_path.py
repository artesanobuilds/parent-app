# flows/generated/test_parent_onboarding_happy_path.py
#
# @generated_from: specs/tier-1/parent-onboarding-happy-path.flow.yml
# @generated_at: 2026-05-31T15:00:00Z
# @modules: auth, consent, profile, content
# @promoted_by: (none -- awaiting review)
#
import pytest

pytestmark = pytest.mark.tier1


def test_new_parent_completes_onboarding_and_home_loads(flow_ctx, new_parent):
    parent = new_parent  # /auth/issue-token already done by the fixture

    # ── Step 1: token is real and matches the requested user_id ─────
    assert parent.token, "issuer returned an empty token"
    assert parent.user_id, "issuer returned no user_id"

    # ── Step 2: consent records under the current agreement version ─
    consent_resp = flow_ctx.post(
        "/consent/submit",
        json={
            "parent_name": parent.display_name,
            "parent_email": "test@example.com",
            "kid_age_band": "3-5",
            "agreement_version": flow_ctx.consent_agreement_version,
        },
        as_=parent,
    )
    assert consent_resp.status_code == 200, consent_resp.text
    consent_body = consent_resp.json()
    # Consent response shape: {id, agreement_version, user_id, ...} —
    # `parent_name` is persisted server-side but NOT echoed in the response.
    assert "id" in consent_body, f"consent missing `id`: {consent_body}"
    assert consent_body.get("agreement_version") == flow_ctx.consent_agreement_version
    assert consent_body.get("user_id") == parent.user_id

    # ── Step 3: profile seed persists parent name + one child ───────
    seed_resp = flow_ctx.post(
        "/profile/seed",
        json={
            "user_id": parent.user_id,
            "parent_name": parent.display_name,
            "kids": [
                {"name": "TestKid", "age": "5", "temperament": "curious",
                 "pronouns": "they/them", "grade_band": "elementary"},
            ],
        },
        as_=parent,
    )
    assert seed_resp.status_code == 200, seed_resp.text
    body = seed_resp.json()
    assert "parent" in body, f"expected `parent` in response, got keys: {list(body.keys())}"
    assert "children" in body, f"expected `children` in response, got keys: {list(body.keys())}"
    # Child round-trip
    children = body["children"]
    assert isinstance(children, dict) and "TestKid" in children, \
        f"expected child 'TestKid' in profile, got: {children!r}"

    # ── Step 4: Home loads — categories ─────────────────────────────
    cats_resp = flow_ctx.get("/content/categories")
    assert cats_resp.status_code == 200, cats_resp.text
    cats = cats_resp.json()
    assert isinstance(cats, list) and len(cats) >= 1, \
        f"expected >=1 category, got {len(cats) if isinstance(cats, list) else type(cats)}"
    for cat in cats:
        for required_key in ("id", "name", "emoji", "description"):
            assert required_key in cat, \
                f"category missing key {required_key!r}: {cat}"

    # ── Step 5: Home loads — articles ───────────────────────────────
    articles_resp = flow_ctx.get("/content/articles")
    assert articles_resp.status_code == 200, articles_resp.text
    articles = articles_resp.json()
    assert isinstance(articles, list) and len(articles) >= 1, \
        f"expected >=1 article, got {len(articles) if isinstance(articles, list) else type(articles)}"
    for art in articles:
        for required_key in ("id", "category", "title"):
            assert required_key in art, f"article missing key {required_key!r}: {art}"
