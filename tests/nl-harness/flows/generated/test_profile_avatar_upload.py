# flows/generated/test_profile_avatar_upload.py
#
# @generated_from: specs/tier-2/profile-avatar-upload.flow.yml
# @generated_at: 2026-07-18T23:30:00Z
# @modules: blobs, profile
# @promoted_by: (none -- awaiting review)
#
import httpx
import pytest

pytestmark = pytest.mark.tier2

# A minimal JPEG-looking payload — the backend validates mime/size claims, the
# bucket stores bytes; neither decodes the image.
FAKE_JPEG = b"\xff\xd8\xff\xe0harness-avatar-bytes"


def _presign(flow_ctx, parent, **overrides):
    payload = {"kind": "avatar", "content_type": "image/jpeg", "byte_size": len(FAKE_JPEG)}
    payload.update(overrides)
    return flow_ctx.post("/blobs/upload-url", json=payload, as_=parent)


def test_avatar_upload_attach_and_sweep(flow_ctx, new_parent):
    parent = new_parent

    # ── self-skip when the target backend has no bucket wired ───────
    presign = _presign(flow_ctx, parent)
    if presign.status_code == 503:
        pytest.skip("blob storage not configured on this backend (BLOB_* unset)")
    assert presign.status_code == 200, presign.text
    key, put_url = presign.json()["key"], presign.json()["url"]
    assert key.startswith(f"u/{parent.user_id}/avatar/"), key

    # ── input validation ────────────────────────────────────────────
    assert _presign(flow_ctx, parent, content_type="image/gif").status_code == 400
    assert _presign(flow_ctx, parent, byte_size=9_000_000).status_code == 400
    assert _presign(flow_ctx, parent, kind="ingest").status_code == 400

    # ── the kid must exist before anything can be attached ──────────
    seed = flow_ctx.post(
        "/profile/seed",
        json={"user_id": parent.user_id, "parent_name": parent.display_name,
              "kids": [{"name": "AvatarKid", "age": "6"}]},
        as_=parent,
    )
    assert seed.status_code == 200, seed.text

    # ── PUT the bytes straight to the bucket (presigned, no auth) ───
    put = httpx.put(put_url, content=FAKE_JPEG,
                    headers={"Content-Type": "image/jpeg"}, timeout=30.0)
    assert put.status_code in (200, 201, 204), f"bucket PUT failed: {put.status_code}"

    # ── security boundaries ─────────────────────────────────────────
    foreign = flow_ctx.post(
        "/profile/kids/AvatarKid/avatar",
        json={"key": "u/some-other-family/avatar/steal.jpg"},
        as_=parent,
    )
    assert foreign.status_code == 403, "foreign-prefix key must be rejected"
    ghost = flow_ctx.post("/profile/kids/GhostKid/avatar", json={"key": key}, as_=parent)
    assert ghost.status_code == 404, "attach must never CREATE a kid"

    # ── attach + presigned read-back ────────────────────────────────
    attach = flow_ctx.post("/profile/kids/AvatarKid/avatar", json={"key": key}, as_=parent)
    assert attach.status_code == 200, attach.text
    kid = attach.json()["children"]["AvatarKid"]
    assert kid.get("avatar_key") == key
    assert kid.get("avatar_url"), "GET-path must serve a presigned avatar_url"

    # avatar_key must NOT be PATCHable (the whitelist subtraction).
    patched = flow_ctx.patch(
        "/profile/kids/AvatarKid",
        json={"avatar_key": "u/some-other-family/avatar/steal.jpg", "temperament": "sunny"},
        as_=parent,
    )
    assert patched.json()["children"]["AvatarKid"]["avatar_key"] == key

    # ── the deletion promise: family delete sweeps the photo prefix ─
    deleted = flow_ctx.delete(f"/family/{parent.user_id}", as_=parent)
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["deleted"].get("blobs", 0) >= 1, deleted.json()
