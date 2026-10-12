#!/usr/bin/env python3
"""Compare selected ElevenLabs settings; --apply/--restore are explicit writes.

Uses environment credentials only. Never prints remote payloads or identifiers.
Backups contain selected prior values, must live outside the checkout, and are
created exclusively with mode 0600. No TTS field is ever patched.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

import httpx

ROOT = Path(__file__).resolve().parents[2]
API = "https://api.elevenlabs.io/v1/convai/agents/"
PREFIX = "conversation_config.turn."
TARGET = {
    PREFIX + "turn_timeout": 7.0,
    PREFIX + "retranscribe_on_turn_timeout": False,
    PREFIX + "soft_timeout_config.timeout_seconds": 1.0,
    PREFIX + "soft_timeout_config.message": "Let me think.",
    PREFIX + "soft_timeout_config.additional_soft_timeout_messages": [
        "Hmm.",
        "Let's see.",
        "I'm thinking.",
        "Hmm, let me see.",
        "Okay, let's see.",
        "Let me find the words.",
        "Let me put that into words.",
    ],
    PREFIX + "soft_timeout_config.randomize_fillers": True,
    PREFIX + "soft_timeout_config.use_llm_generated_message": False,
}
COMPARE = tuple(TARGET) + tuple("conversation_config." + key for key in (
    "turn.turn_eagerness", "turn.turn_model", "turn.speculative_turn",
    "tts.model_id", "tts.stability", "tts.similarity_boost", "tts.speed",
    "tts.optimize_streaming_latency",
))
MISSING = object()


class ConfigError(RuntimeError):
    """Safe operator-facing error; never includes remote response bodies."""


def value_at(payload, path):
    value = payload
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return MISSING
        value = value[key]
    return value


def selected(payload):
    result = {path: value_at(payload, path) for path in TARGET}
    if any(value is MISSING for value in result.values()):
        raise ConfigError("Selected fields are missing; exact restoration cannot be guaranteed. No patch sent.")
    validate_values(result)
    return deepcopy(result)


def validate_values(values):
    if not isinstance(values, dict) or set(values) != set(TARGET):
        raise ConfigError("Backup has an invalid selected-field allowlist.")
    for path, expected in TARGET.items():
        value = values[path]
        valid = (type(value) in (int, float) if type(expected) is float else type(value) is type(expected))
        if isinstance(expected, list):
            valid = valid and all(isinstance(item, str) for item in value)
        if not valid:
            raise ConfigError("Selected settings have unsupported types; no patch sent.")


def patch_for(values):
    validate_values(values)
    patch = {}
    for path, value in values.items():
        branch = patch
        keys = path.split(".")
        for key in keys[:-1]:
            branch = branch.setdefault(key, {})
        branch[keys[-1]] = deepcopy(value)
    return patch


def compare(kid, parent):
    rows = []
    for path in COMPARE:
        left, right = value_at(kid, path), value_at(parent, path)
        row = {"field": path, "kid_present": left is not MISSING,
               "parent_present": right is not MISSING,
               "equal": left is not MISSING and right is not MISSING and left == right}
        if path in TARGET:
            row["kid_matches_target"] = left is not MISSING and left == TARGET[path]
        rows.append(row)
    return {"mode": "compare", "fields": rows, "tts_requires_listening": True}


def request(client, method, agent_id, **kwargs):
    # IDs are environment configuration, never an arbitrary URL/path override.
    if not agent_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in agent_id):
        raise ConfigError("Invalid agent identity configuration.")
    try:
        response = client.request(method, API + agent_id, **kwargs)
        if not response.is_success:
            raise ConfigError(f"Provider request failed (HTTP {response.status_code}); inspect privately.")
        return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise ConfigError("Provider request or JSON decoding failed; inspect privately.") from None


def identity_digest(agent_id):
    return hashlib.sha256(agent_id.encode()).hexdigest()


def private_path(path):
    path = Path(path).expanduser()
    if path.is_symlink():
        raise ConfigError("Backup must not be a symlink.")
    path = path.resolve()
    if path == ROOT or ROOT in path.parents:
        raise ConfigError("Backup must be outside the checkout.")
    if not path.parent.is_dir() or stat.S_IMODE(path.parent.stat().st_mode) & 0o077:
        raise ConfigError("Backup parent must already be a private directory (mode 0700).")
    return path


def save_backup(path, agent_id, before, after):
    path = private_path(path)
    payload = {"schema": 1, "target_sha256": identity_digest(agent_id),
               "created_at": datetime.now(timezone.utc).isoformat(),
               "before": before, "after": after}
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as stream:
            json.dump(payload, stream, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
    except (OSError, ValueError):
        raise ConfigError("Private backup could not be created; no patch sent.") from None


def load_backup(path, agent_id):
    path = private_path(path)
    try:
        if stat.S_IMODE(path.stat().st_mode) & 0o077:
            raise ConfigError("Backup must be private (mode 0600).")
        payload = json.loads(path.read_text())
        if set(payload) != {"schema", "target_sha256", "created_at", "before", "after"}:
            raise ConfigError("Invalid backup structure.")
        if payload["schema"] != 1 or payload["target_sha256"] != identity_digest(agent_id):
            raise ConfigError("Backup does not match this kid agent.")
        validate_values(payload["before"])
        validate_values(payload["after"])
        if payload["after"] != TARGET:
            raise ConfigError("Backup target does not match this tool version.")
        return payload
    except (OSError, ValueError, TypeError):
        raise ConfigError("Could not read a valid private backup.") from None


def patch_and_verify(client, kid_id, expected):
    request(client, "PATCH", kid_id, json=patch_for(expected))
    actual = request(client, "GET", kid_id)
    if any(value_at(actual, path) != value for path, value in expected.items()):
        raise ConfigError("Readback mismatch: update is unverified. Keep the backup and inspect or restore; no automatic retry.")
    return actual


def verified_report(mode, actual):
    cap = value_at(actual, PREFIX + "soft_timeout_config.max_soft_timeouts_per_generation")
    return {
        "mode": mode, "verified": True, "fields": list(TARGET),
        "observed_filler_cap": cap if type(cap) is int else None,
        "note": "Only the seven selected values are verified. The provider may normalize unsent fields, including the filler cap; those fields are not restored by this tool.",
    }


def run(options, client, kid_id, parent_id):
    kid = request(client, "GET", kid_id)
    if options.restore:
        backup = load_backup(options.restore, kid_id)
        current = selected(kid)
        # Allow retry after a partial PATCH/readback failure, but never overwrite
        # a third-party edit to one of our selected fields.
        if any(current[path] not in (backup["before"][path], backup["after"][path]) for path in TARGET):
            raise ConfigError("Selected settings drifted since backup; restore refused pending review.")
        actual = patch_and_verify(client, kid_id, backup["before"])
        return verified_report("restore", actual)
    parent = request(client, "GET", parent_id)
    if not options.apply:
        return compare(kid, parent)
    if kid_id == parent_id:
        raise ConfigError("Kid and parent identities must differ; no patch sent.")
    before = selected(kid)
    save_backup(options.backup, kid_id, before, TARGET)
    # Catch an operator edit between inventory and backup before changing it.
    if selected(request(client, "GET", kid_id)) != before:
        raise ConfigError("Selected settings changed during preparation; no patch sent.")
    actual = patch_and_verify(client, kid_id, TARGET)
    return verified_report("apply", actual)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true")
    mode.add_argument("--restore", metavar="PRIVATE_BACKUP")
    parser.add_argument("--backup", help="New private backup path; required only with --apply")
    options = parser.parse_args(argv)
    if options.apply and not options.backup:
        parser.error("--apply requires --backup")
    if options.backup and not options.apply:
        parser.error("--backup requires --apply")
    try:
        api_key = os.environ.get("ELEVENLABS_API_KEY", "")
        kid_id = os.environ.get("ELEVENLABS_AGENT_ID", "")
        parent_id = os.environ.get("ELEVENLABS_PARENT_AGENT_ID", "")
        if not api_key or not kid_id or (not options.restore and not parent_id):
            raise ConfigError("Required ElevenLabs environment configuration is missing.")
        with httpx.Client(headers={"xi-api-key": api_key}, timeout=20, follow_redirects=False) as client:
            result = run(options, client, kid_id, parent_id)
        print(json.dumps(result, indent=2))
        return 0
    except (ConfigError, OSError):
        # ConfigError messages are locally authored and contain no payload/ID.
        exc = sys.exc_info()[1]
        print(str(exc) if isinstance(exc, ConfigError) else "Local file operation failed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
