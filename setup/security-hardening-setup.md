# Security Hardening Setup

The security hardening pass (2026-07). Covers the operator config + procedures
for the admin gate, security headers, rate limits, secrets scanning, data-subject
deletion, and at-rest encryption. Code is in the repo; this is the external
config + how to run the recurring checks.

See also: [auth-setup.md](auth-setup.md) (the biggest security item — sign-in +
migration) and the app-layer invariants enforced by tests in `mvp-backend/tests/`
(`test_bola_sweep.py`, `test_admin_session.py`, `test_security_headers.py`,
`test_tool_scoping_guard.py`).

---

## 1. Admin / CMS operator gate

The CMS no longer bakes the admin token into its JS bundle (it did — every CMS
visitor could read the operator secret). It now uses an **HttpOnly cookie
session** minted by `POST /admin/session`; scripts/CI still use the
`X-Admin-Token` header. Both accepted by `app/admin_auth.py`.

| Var | Value | Notes |
| --- | --- | --- |
| `ADMIN_TOKEN` | `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` | **Secret.** Unlocks `/cms/*` + `/data/*`. Rotating it instantly invalidates all CMS sessions (the cookie is bound to a fingerprint of the token). |
| `ADMIN_SESSION_TTL_SECONDS` | `43200` (12h, default) | CMS cookie session lifetime. |
| `ADMIN_COOKIE_SECURE` | `1` (prod) | `0` only for local http. |

**Rotate the admin token (do this as part of a deploy):**
```bash
cd mvp-backend
NEW=$(python3 -c "import secrets;print(secrets.token_urlsafe(32))")
railway variables --set "ADMIN_TOKEN=$NEW" --skip-deploys
# update local .env too, then deploy. Re-log into the CMS with the new token.
```
Also ensure **`VITE_ADMIN_TOKEN` is NOT set** in Railway or the CMS build — it's
obsolete and would only ship a secret into the browser bundle.

---

## 2. Security response headers + HSTS

`app/security_headers.py` adds `X-Content-Type-Options: nosniff`,
`Referrer-Policy`, `X-Frame-Options: DENY`, `Permissions-Policy`, a CSP on the
served SPAs, and (gated) HSTS.

| Var | Value | Notes |
| --- | --- | --- |
| `ENABLE_HSTS` | `1` in prod, `0` local | HSTS pins HTTPS for a year; only safe where TLS is terminated (Railway). Never set on plain-http local dev. |
| `ALLOWED_ORIGINS` | `https://<web+dashboard origins>` | CORS allow-list; never `*`. |
| `TRUST_PROXY` | `1` (behind Railway's proxy) | Enables `X-Forwarded-For` parsing for real client IP in rate limiting. |

Verify on prod: `curl -sD - -o /dev/null https://<host>/health | grep -i strict-transport`.

---

## 3. Rate limits

In-memory token buckets (`app/rate_limit.py`), all env-tunable. Prod values:

| Var | Prod value |
| --- | --- |
| `RATE_LIMIT_AUTH_PER_HOUR` | `60` |
| `RATE_LIMIT_CHAT_PER_MIN` | `60` |
| `RATE_LIMIT_CONFIG_PER_MIN` | `30` |
| `RATE_LIMIT_RESEARCH_PER_HOUR` | `20` |

(Note: per-process — resets on deploy and doesn't share across replicas. Swap for
Redis before running multiple backend replicas.)

---

## 4. Secrets scanning (gitleaks + trufflehog)

Install + run a full-history scan (do this once, and any time before opening the
repo up):
```bash
brew install gitleaks
cd <repo-root>
gitleaks git --no-banner          # respects .gitleaks.toml allowlist
# verified-secret sweep (optional, needs trufflehog):
# trufflehog git file://. --only-verified
git log --all --diff-filter=A -- '*.p8'   # confirm no APNs key was ever committed
```
`.gitleaks.toml` at the repo root allowlists verified false positives (design-
token CSS names, a vendored third-party JS bundle, a docs placeholder). The
2026-07 scan found **no real committed secrets**. If a scan ever finds a real
one: **rotate it** (regenerate the key/token) — removing it from history is not
enough once it's been pushed.

Secrets live in Railway env + gitignored files (`.env`, `*.p8`,
`mvp-backend/secrets/*`). `env.example` is the canonical catalog of every var.

---

## 5. Data-subject deletion (right to be forgotten)

`DELETE /family/{user_id}` cascades every kid-data table, **re-exports the parquet
snapshots immediately** (so they don't retain deleted PII until the next export),
and — when PostHog is configured — deletes the PostHog person + events too
(`app/analytics/deletion.py`). Only the audit-event row survives.

---

## 6. At-rest encryption (Phase 4 — planned, not yet enabled)

Railway volumes are **not** software-encrypted, so the DuckDB file + parquet
snapshots are plaintext at rest. DuckDB 1.4+ supports transparent AES-256; the
plan is to gate it on `DUCKDB_ENCRYPTION_KEY` (32-byte base64, Railway env only —
**lose the key = lose the volume**). Not implemented yet; when it lands it needs
a staging rehearsal on a copy of the prod volume + a volume snapshot before the
cutover. Tracked in the plan.

---

## 7. Security CI (Phase 5 — planned, needs a GitHub remote)

The repo has no GitHub remote yet. When pushed, add `.github/workflows/security.yml`
(pip-audit, bandit, semgrep, gitleaks, osv-scanner, trivy on the image) + enable
Dependabot security updates, secret-scanning push protection, and CodeQL. Tracked
in the plan.
