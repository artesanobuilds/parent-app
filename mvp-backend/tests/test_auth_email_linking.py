"""Cross-provider account linking by VERIFIED email.

2026-08-09: Miguel signed in with Google via "I already have an account" and
was routed back through onboarding instead of Home. `auth_identities` held
apple → user A (real profile, 3 `user_data` rows) and google → user B (a
brand-new, empty user_id) — same email, two accounts, because the first-ever
Google sign-in for that email had no way to find the existing Apple account.

`resolve_account` (app/auth_router.py) now checks
`find_identity_user_by_verified_email` before minting a fresh user_id — see
its doc comment for why the check has to be verified-only in both directions.

Uses the same monkeypatched-provider idiom as test_auth_v2.py (`fake_apple`)
and test_auth_google_pairing.py (`login_google.mint_login_code` for the
Google side, which carries its own email + email_verified).
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("MVP_DUCKDB_PATH", str(Path(tempfile.mkdtemp()) / "auth_email_link.duckdb"))
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy")
os.environ.setdefault("AUTH_JWT_SECRET", "test-jwt-secret-email-link")

from fastapi.testclient import TestClient  # noqa: E402

import app.server as server  # noqa: E402
import app.auth_router as auth_router  # noqa: E402
import app.auth_login_google as login_google  # noqa: E402


@pytest.fixture(scope="module")
def client():
    from app.duckdb_storage import DuckDBStorage
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)
    with TestClient(server.app) as c:
        yield c
    server.storage_backend = DuckDBStorage(db_path=server.storage_backend.db_path)


@pytest.fixture
def fake_apple(monkeypatch):
    """`verify('apple', token)` returns a FIXED identity per token, with a
    controllable email — same shape as test_auth_v2.py's fixture, but the
    email/verified flag are set per test rather than derived from the token,
    so a test can put two providers on the SAME address."""
    identities: dict[str, tuple[str, str, bool]] = {}

    def _verify(provider, id_token, nonce=None):
        assert provider == "apple"
        return identities[id_token]

    monkeypatch.setattr(auth_router.auth_providers, "verify", _verify)
    return identities


def _google_code(provider_sub: str, email: str, verified: bool = True) -> str:
    return login_google.mint_login_code(
        provider="google", provider_sub=provider_sub,
        email=email, email_verified=verified,
    )


# ── The real bug: same email, second provider, first-ever sign-in ───────────

def test_google_after_apple_same_verified_email_links_not_mints(client, fake_apple):
    email = "miguel@example.com"
    fake_apple["apple-tok-1"] = ("apple-sub-1", email, True)

    apple_login = client.post(
        "/auth/login", json={"provider": "apple", "id_token": "apple-tok-1"},
    )
    assert apple_login.status_code == 200, apple_login.text
    apple_user_id = apple_login.json()["user_id"]
    assert apple_login.json()["is_new_account"] is True

    # Give that account a real profile — the whole point is that Google must
    # land on THIS account, not an empty new one.
    server.storage_backend._con.execute(
        "INSERT OR IGNORE INTO user_data (user_id, name, data) VALUES (?, ?, ?)",
        [apple_user_id, "profile", "{}"],
    )

    code = _google_code("gsub-link-1", email, verified=True)
    google_login = client.post("/auth/exchange-code", json={"login_code": code})
    assert google_login.status_code == 200, google_login.text
    body = google_login.json()

    assert body["user_id"] == apple_user_id, (
        "Google sign-in minted a SECOND account instead of linking to the "
        "existing one at the same verified email — this is the exact bug"
    )
    assert body["is_new_account"] is False
    assert body["linked_by_email"] is True
    assert body["has_profile"] is True, (
        "linked to the right user_id but has_profile is false — the client "
        "would still route to onboarding"
    )

    # Both identities now resolve to the SAME account.
    assert server.storage_backend.get_identity("apple", "apple-sub-1")["user_id"] == apple_user_id
    assert server.storage_backend.get_identity("google", "gsub-link-1")["user_id"] == apple_user_id


def test_signing_in_again_with_the_linked_identity_still_works(client, fake_apple):
    """Once linked, the SECOND provider's identity is a normal identity —
    logging in with it again must NOT re-run the email search (it should hit
    the fast `get_identity` path, same account, no new audit event needed)."""
    email = "repeat@example.com"
    fake_apple["apple-tok-2"] = ("apple-sub-2", email, True)
    apple_user_id = client.post(
        "/auth/login", json={"provider": "apple", "id_token": "apple-tok-2"},
    ).json()["user_id"]

    code1 = _google_code("gsub-repeat-1", email, verified=True)
    first = client.post("/auth/exchange-code", json={"login_code": code1}).json()
    assert first["user_id"] == apple_user_id
    assert first["linked_by_email"] is True

    # A second Google sign-in with the SAME provider_sub (not a new one) —
    # `get_identity` finds it directly, no email search involved.
    code2 = _google_code("gsub-repeat-1", email, verified=True)
    second = client.post("/auth/exchange-code", json={"login_code": code2}).json()
    assert second["user_id"] == apple_user_id
    assert second["is_new_account"] is False
    assert second["linked_by_email"] is False, (
        "a repeat sign-in with an ALREADY-linked identity must take the "
        "existing-identity fast path, not the email-search path"
    )


# ── The guardrails: when linking must NOT happen ─────────────────────────────

def test_unverified_incoming_email_does_not_link(client, fake_apple):
    """An unverified email on the INCOMING (Google) side must never be
    trusted enough to attach to someone else's account, even if it matches a
    verified email on file."""
    email = "unverified@example.com"
    fake_apple["apple-tok-3"] = ("apple-sub-3", email, True)
    apple_user_id = client.post(
        "/auth/login", json={"provider": "apple", "id_token": "apple-tok-3"},
    ).json()["user_id"]

    code = _google_code("gsub-unverified-1", email, verified=False)
    result = client.post("/auth/exchange-code", json={"login_code": code}).json()

    assert result["user_id"] != apple_user_id
    assert result["is_new_account"] is True
    assert result["linked_by_email"] is False


def test_ambiguous_email_across_two_existing_accounts_does_not_link(client, fake_apple):
    """Two DIFFERENT accounts already share an email (both verified). A third
    provider at that email must NOT guess which one to join — same posture as
    `find_account_by_email` elsewhere in this codebase.

    Seeded directly via `link_identity`, bypassing `resolve_account`'s own
    email-linking — going through the normal login flow for both accounts
    would (correctly, per the test above) converge them onto ONE account
    instead of ever producing two, since that convergence is exactly the
    behavior being verified elsewhere in this file. The ambiguity this test
    covers is a state the system should never willingly create but must still
    handle safely if it's already there (e.g. two accounts pre-dating this
    fix, or an address that was never actually confirmed to be exclusive)."""
    email = "shared@example.com"
    storage = server.storage_backend
    storage.link_identity(
        user_id="ambiguous-user-a", provider="apple", provider_sub="ambiguous-sub-a",
        email=email, email_verified=True,
    )
    storage.link_identity(
        user_id="ambiguous-user-b", provider="apple", provider_sub="ambiguous-sub-b",
        email=email, email_verified=True,
    )

    code = _google_code("gsub-ambiguous-1", email, verified=True)
    result = client.post("/auth/exchange-code", json={"login_code": code}).json()

    assert result["user_id"] not in ("ambiguous-user-a", "ambiguous-user-b")
    assert result["is_new_account"] is True
    assert result["linked_by_email"] is False


def test_different_emails_mint_separate_accounts(client, fake_apple):
    """The ordinary case (and what an Apple private-relay address looks like
    in practice): different email on each provider → no match → own account.
    """
    fake_apple["apple-tok-5"] = ("apple-sub-5", "one@example.com", True)
    apple_user_id = client.post(
        "/auth/login", json={"provider": "apple", "id_token": "apple-tok-5"},
    ).json()["user_id"]

    code = _google_code("gsub-different-1", "totally-different@example.com", verified=True)
    result = client.post("/auth/exchange-code", json={"login_code": code}).json()

    assert result["user_id"] != apple_user_id
    assert result["is_new_account"] is True
    assert result["linked_by_email"] is False


def test_legacy_claim_wins_over_email_match(client, fake_apple):
    """If BOTH an explicit legacy-token claim and an email match would apply,
    the legacy claim wins — it is a stronger, explicit proof of ownership,
    and it targets a SPECIFIC user_id rather than a lookup result."""
    email = "legacy-precedence@example.com"
    fake_apple["apple-tok-6"] = ("apple-sub-6", email, True)
    apple_user_id = client.post(
        "/auth/login", json={"provider": "apple", "id_token": "apple-tok-6"},
    ).json()["user_id"]

    # A SEPARATE legacy account, unrelated email, with a valid opaque token.
    legacy_token = client.post(
        "/auth/issue-token", json={"user_id": "legacy-precedence-user"},
    ).json()["token"]

    code = _google_code("gsub-legacy-precedence-1", email, verified=True)
    result = client.post("/auth/exchange-code", json={
        "login_code": code,
        "legacy_user_id": "legacy-precedence-user", "legacy_token": legacy_token,
    }).json()

    assert result["user_id"] == "legacy-precedence-user", (
        "the explicit legacy claim must win over the email match"
    )
    assert result["user_id"] != apple_user_id
    assert result["linked_legacy"] is True
    assert result["linked_by_email"] is False


# ── The storage primitive, directly ──────────────────────────────────────────

def test_find_identity_user_by_verified_email_storage_primitive():
    storage = server.storage_backend
    storage.link_identity(
        user_id="direct-user-1", provider="apple", provider_sub="direct-sub-1",
        email="Direct@Example.com", email_verified=True,
    )

    # Case-insensitive, whitespace-tolerant — same normalization idiom as
    # find_account_by_email.
    assert storage.find_identity_user_by_verified_email(" direct@example.com ") == "direct-user-1"
    assert storage.find_identity_user_by_verified_email("nobody@example.com") is None
    assert storage.find_identity_user_by_verified_email(None) is None
    assert storage.find_identity_user_by_verified_email("") is None

    # An UNVERIFIED identity at an email must not be found by this lookup —
    # it exists specifically to gate on email_verified.
    storage.link_identity(
        user_id="direct-user-2", provider="google", provider_sub="direct-sub-2",
        email="notverified@example.com", email_verified=False,
    )
    assert storage.find_identity_user_by_verified_email("notverified@example.com") is None
