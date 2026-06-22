"""Daily Gmail sync agent (R3).

For each connected Gmail account, pulls emails FROM the parent's registered camps
(`confirmed`/`signed_up`), runs them through the existing `ExtractedActivity`
extractor, and attaches the details (calendar entries, payment/form to-dos,
welcome-letter links) to that activity. Idempotent via `ingest_artifacts.external_id`.
Driven by `EmailSyncWorker` (daily schedule + force-trigger) and operated from the
CMS (`/cms/email-sync/*`).
"""
