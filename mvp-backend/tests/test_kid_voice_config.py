"""No vendor calls: validate the operator tool against a recording HTTP transport."""
from argparse import Namespace
from copy import deepcopy
import json
import stat

import httpx
import pytest

from tools import kid_voice_config as config


def payload():
    values = deepcopy(config.TARGET)
    values[config.PREFIX + "turn_timeout"] = 10.0
    values[config.PREFIX + "soft_timeout_config.timeout_seconds"] = -1.0
    result = config.patch_for(values)
    result["conversation_config"]["tts"] = {"voice_id": "private-voice", "model_id": "keep-this-model"}
    result["conversation_config"]["agent"] = {"prompt": {"prompt": "private prompt"}}
    result["conversation_config"]["turn"]["unrelated_option"] = "preserve"
    result["private_api_key"] = "never-print-this"
    return result


def merge(target, patch):
    for key, value in patch.items():
        if isinstance(value, dict):
            merge(target.setdefault(key, {}), value)
        else:
            target[key] = deepcopy(value)


class Provider:
    def __init__(self, *, ignore_patch=False):
        self.kid = payload()
        self.parent = payload()
        self.calls = []
        self.ignore_patch = ignore_patch

    def handle(self, request):
        body = json.loads(request.content) if request.content else None
        self.calls.append((request.method, request.url.path, body))
        if request.method == "PATCH":
            assert request.url.path.endswith("/private-kid")
            if not self.ignore_patch:
                merge(self.kid, body)
        return httpx.Response(200, json=self.kid if request.url.path.endswith("/private-kid") else self.parent)

    def client(self):
        return httpx.Client(transport=httpx.MockTransport(self.handle))


def options(*, apply=False, backup=None, restore=None):
    return Namespace(apply=apply, backup=backup, restore=restore)


@pytest.fixture
def backup(tmp_path):
    folder = tmp_path / "private"
    folder.mkdir(mode=0o700)
    return folder / "prior.json"


def test_default_main_is_read_only_and_never_prints_payload_or_ids(monkeypatch, capsys):
    provider = Provider()
    client = provider.client()
    monkeypatch.setattr(config.httpx, "Client", lambda **kwargs: client)
    monkeypatch.setenv("ELEVENLABS_API_KEY", "secret-api-key")
    monkeypatch.setenv("ELEVENLABS_AGENT_ID", "private-kid")
    monkeypatch.setenv("ELEVENLABS_PARENT_AGENT_ID", "private-parent")
    assert config.main([]) == 0
    output = capsys.readouterr().out
    assert [method for method, _, _ in provider.calls] == ["GET", "GET"]
    for private in ("private-kid", "private-parent", "private-voice", "secret-api-key", "private prompt", "never-print-this"):
        assert private not in output
    assert json.loads(output)["mode"] == "compare"


def test_apply_patches_only_selected_kid_leaves_and_restore_is_exact(backup):
    provider = Provider()
    original = deepcopy(provider.kid)
    with provider.client() as client:
        result = config.run(options(apply=True, backup=backup), client, "private-kid", "private-parent")
        assert result["verified"]
        patches = [body for method, _, body in provider.calls if method == "PATCH"]
        assert patches == [config.patch_for(config.TARGET)]
        assert provider.kid["conversation_config"]["tts"] == original["conversation_config"]["tts"]
        assert provider.kid["conversation_config"]["agent"] == original["conversation_config"]["agent"]
        assert provider.kid["conversation_config"]["turn"]["unrelated_option"] == "preserve"
        assert stat.S_IMODE(backup.stat().st_mode) == 0o600
        saved = json.loads(backup.read_text())
        assert saved["before"] == config.selected(original)
        assert "private-kid" not in backup.read_text()
        assert "private prompt" not in backup.read_text()
        assert config.run(options(restore=backup), client, "private-kid", "private-parent")["verified"]
    assert provider.kid == original
    assert provider.calls[-1][0] == "GET"  # Restore verified independently.


def test_readback_mismatch_fails_and_keeps_backup(backup):
    provider = Provider(ignore_patch=True)
    with provider.client() as client, pytest.raises(config.ConfigError, match="Readback mismatch"):
        config.run(options(apply=True, backup=backup), client, "private-kid", "private-parent")
    assert backup.exists()
    assert sum(method == "PATCH" for method, _, _ in provider.calls) == 1


def test_missing_field_refuses_apply_before_backup_or_patch(backup):
    provider = Provider()
    del provider.kid["conversation_config"]["turn"]["retranscribe_on_turn_timeout"]
    with provider.client() as client, pytest.raises(config.ConfigError, match="fields are missing"):
        config.run(options(apply=True, backup=backup), client, "private-kid", "private-parent")
    assert not backup.exists()
    assert all(method == "GET" for method, _, _ in provider.calls)


def test_existing_backup_cannot_be_overwritten(backup):
    backup.write_text("keep me")
    provider = Provider()
    with provider.client() as client, pytest.raises(config.ConfigError, match="could not be created"):
        config.run(options(apply=True, backup=backup), client, "private-kid", "private-parent")
    assert backup.read_text() == "keep me"
    assert all(method == "GET" for method, _, _ in provider.calls)


def test_restore_refuses_target_mismatch_and_selected_drift(backup):
    provider = Provider()
    with provider.client() as client:
        config.run(options(apply=True, backup=backup), client, "private-kid", "private-parent")
        with pytest.raises(config.ConfigError, match="does not match"):
            config.run(options(restore=backup), client, "other-kid", "private-parent")
        provider.kid["conversation_config"]["turn"]["turn_timeout"] = 12
        with pytest.raises(config.ConfigError, match="drifted"):
            config.run(options(restore=backup), client, "private-kid", "private-parent")
    assert sum(method == "PATCH" for method, _, _ in provider.calls) == 1


def test_private_backup_constraints(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "ROOT", tmp_path)
    inside = tmp_path / "private"
    inside.mkdir(mode=0o700)
    with pytest.raises(config.ConfigError, match="outside the checkout"):
        config.private_path(inside / "backup.json")
    monkeypatch.setattr(config, "ROOT", tmp_path / "checkout")
    inside.chmod(0o755)
    with pytest.raises(config.ConfigError, match="0700"):
        config.private_path(inside / "backup.json")


def test_provider_failure_never_echoes_url_or_body():
    def fail(request):
        return httpx.Response(403, text="private-agent-id and secret-api-key")
    with httpx.Client(transport=httpx.MockTransport(fail)) as client:
        with pytest.raises(config.ConfigError) as exc:
            config.request(client, "GET", "private-kid")
    assert str(exc.value) == "Provider request failed (HTTP 403); inspect privately."


def test_reports_provider_normalized_unsent_filler_cap_on_apply_and_restore(backup):
    provider = Provider()
    soft = provider.kid["conversation_config"]["turn"]["soft_timeout_config"]
    soft["max_soft_timeouts_per_generation"] = 1
    original_handle = provider.handle

    def normalizing_provider(request):
        if request.method == "PATCH":
            soft["max_soft_timeouts_per_generation"] = 3
        return original_handle(request)

    with httpx.Client(transport=httpx.MockTransport(normalizing_provider)) as client:
        applied = config.run(options(apply=True, backup=backup), client, "private-kid", "private-parent")
        restored = config.run(options(restore=backup), client, "private-kid", "private-parent")
    for report in (applied, restored):
        assert report["verified"]
        assert report["observed_filler_cap"] == 3
        assert "normalize unsent fields" in report["note"]
    for method, _, body in provider.calls:
        if method == "PATCH":
            assert "max_soft_timeouts_per_generation" not in json.dumps(body)
    assert "max_soft_timeouts_per_generation" not in backup.read_text()


def test_unavailable_or_unexpected_filler_cap_is_not_dumped():
    assert config.verified_report("apply", {})["observed_filler_cap"] is None
    unexpected = config.patch_for(config.TARGET)
    unexpected["conversation_config"]["turn"]["soft_timeout_config"]["max_soft_timeouts_per_generation"] = {"private": "do not print"}
    report = config.verified_report("apply", unexpected)
    assert report["observed_filler_cap"] is None
    assert "do not print" not in json.dumps(report)
