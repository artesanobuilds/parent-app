"""Token prefetch must not claim that a child heard a greeting."""
import asyncio
from types import SimpleNamespace


def test_greeting_requires_a_child_turn_for_returning(monkeypatch):
    from app import server
    history = []
    config = {'id': 'kid-greeting', 'invariants': {'agent_display_name': 'Pebble'}}
    monkeypatch.setattr(server, 'storage_backend', SimpleNamespace(
        get_kid_messages=lambda *a, **k: history))
    first = server._kid_voice_greeting('Sam', config)
    assert "I'm Pebble" in first
    history.append({'role': 'assistant', 'content': first})
    assert server._kid_voice_greeting('Sam', config) == first
    history.append({'role': 'user', 'content': 'hello'})
    assert 'Hi again, Sam' in server._kid_voice_greeting('Sam', config)


def test_token_prefetch_uses_current_voice_prompt_without_transcript_write(monkeypatch):
    import httpx
    from app import server
    config = {'id': 'kid-greeting', 'enabled': True, 'system_prompt': 'STALE',
              'invariants': {'agent_display_name': 'Pebble', 'persona_examples': ['old greeting']}}
    store = SimpleNamespace(
        get_kid_agent_config=lambda *a: config,
        is_kid_agent_crisis_locked=lambda *a: None,
        get_kid_messages=lambda *a, **k: [],
    )  # Deliberately no append method: minting a token cannot write history.
    monkeypatch.setattr(server, 'storage_backend', store)
    monkeypatch.setattr(server, '_require_consent', lambda *a: None)
    monkeypatch.setattr(server, '_verify_kid_pin', lambda *a: True)
    monkeypatch.setattr(server, '_track', lambda *a, **k: None)
    monkeypatch.setenv('ELEVENLABS_AGENT_ID', 'fixture-agent')
    monkeypatch.setenv('ELEVENLABS_API_KEY', 'fixture-key')
    calls = []
    def prompt(uid, kid, approved, *, surface):
        calls.append((uid, kid, approved, surface))
        return 'CURRENT VOICE POLICY'
    monkeypatch.setattr(server.kid_agent_service, 'build_effective_prompt', prompt)
    class Client:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): pass
        async def get(self, *a, **k):
            return SimpleNamespace(status_code=200, json=lambda: {'token': 'fixture-token'})
    monkeypatch.setattr(httpx, 'AsyncClient', Client)
    for _ in range(2):
        result = asyncio.run(server.voice_convai_token(kid_name='Sam', user_id='family', x_kid_pin=None))
        assert set(result) == {'signed_url', 'conversation_config_override', 'custom_llm_extra_body'}
        agent = result['conversation_config_override']['agent']
        assert agent['prompt']['prompt'] == 'CURRENT VOICE POLICY'
        assert "I'm Pebble" in agent['first_message']
        assert result['custom_llm_extra_body']['thread_id'] == 'default'
    assert all(call == ('family', 'Sam', config, 'voice') for call in calls)
