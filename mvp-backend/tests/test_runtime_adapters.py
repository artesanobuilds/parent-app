import json
from types import SimpleNamespace

from app.agent_runtime.adapters.text import DONE, encode
from app.agent_runtime.adapters.voice import _LinkStripper
from app.agent_runtime.events import RunEvent, normalize


def test_text_envelopes_retain_bytes_and_order():
    events = [RunEvent('token', content='hello'), RunEvent('tool_start', tool='save'),
              RunEvent('tool_end', tool='save'), RunEvent('error', content='failed')]
    assert [encode(e) for e in events] == [
        'data: {"type": "token", "content": "hello"}\n\n',
        'data: {"type": "tool_start", "tool": "save"}\n\n',
        'data: {"type": "tool_end", "tool": "save"}\n\n',
        'data: {"type": "error", "content": "failed"}\n\n',
    ]
    assert DONE == 'data: [DONE]\n\n'


def test_normalizer_drops_nontext_model_blocks():
    assert normalize({'event': 'on_chat_model_stream', 'data': {
        'chunk': SimpleNamespace(content=[{'type': 'tool_use'}])}}) is None
    assert normalize({'event': 'on_chain_end'}) is None


def test_voice_strips_every_split_of_content_link():
    value = 'Read [Gentle limits](mvp://library/article-7) today.'
    for index in range(len(value)):
        stripper = _LinkStripper()
        first, tools1 = stripper.feed(value[:index])
        second, tools2 = stripper.feed(value[index:])
        assert first + second + stripper.flush() == 'Read Gentle limits today.'
        assert tools1 + tools2 == [('library', 'article-7')]
