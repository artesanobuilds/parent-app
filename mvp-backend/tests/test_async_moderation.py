"""Offline async safety gates: scheduling, deadlines, precedence and rubrics."""
import asyncio
from types import SimpleNamespace

import pytest

from app import moderation as m


def allowed():
    return m.ModerationResult(False, "low", "ok", "test passed", "allow")


def age_ok():
    return m._AgeAppropriateVerdict(age_appropriate=True, confidence=1)


def input_args(text="I miss my goldfish"):
    return dict(user_id="synthetic-parent", kid_name="Test Kid", agent_id="async-test-agent",
                age_band="middle", text=text)


@pytest.fixture(autouse=True)
def clear_switches():
    m.unfreeze_all()
    m.revive_agent("async-test-agent")
    yield
    m.unfreeze_all()
    m.revive_agent("async-test-agent")


def test_native_checks_overlap_and_leave_event_loop_responsive(monkeypatch):
    async def run():
        entered = set()
        both = asyncio.Event()
        release = asyncio.Event()

        async def arrive(name):
            entered.add(name)
            if len(entered) == 2:
                both.set()
            await release.wait()

        async def create(**kwargs):
            assert kwargs['timeout'] == m.MODERATION_REQUEST_TIMEOUT
            await arrive('moderation')
            return SimpleNamespace(results=[SimpleNamespace(flagged=False)])

        async def ainvoke(prompt, config=None):
            await arrive('age')
            return age_ok()

        monkeypatch.setattr(m, '_async_openai_client', lambda: SimpleNamespace(
            moderations=SimpleNamespace(create=create)))
        monkeypatch.setattr(m, '_age_model', lambda: SimpleNamespace(ainvoke=ainvoke))
        task = asyncio.create_task(m.amoderate_input(**input_args()))
        await asyncio.wait_for(both.wait(), 1)
        # The test task can progress while BOTH actual native async seams await.
        await asyncio.sleep(0)
        assert not task.done()
        release.set()
        assert not (await task).flagged
    asyncio.run(run())


@pytest.mark.parametrize('mode,category', [('crisis', 'crisis'), ('freeze', 'frozen'), ('kill', 'killed')])
def test_local_precedence_prevents_all_provider_dispatch(monkeypatch, mode, category):
    async def unexpected(*args, **kwargs):
        pytest.fail('local safety verdict must preempt providers')
    monkeypatch.setattr(m, 'amoderate_with_openai', unexpected)
    monkeypatch.setattr(m, 'aclassify_age_appropriate', unexpected)
    if mode == 'freeze':
        m.freeze_all()
    if mode == 'kill':
        m.kill_agent('async-test-agent')
    verdict = asyncio.run(m.amoderate_input(**input_args('I want to kill myself')))
    assert verdict.flagged and verdict.category == category
    assert verdict.suggested_action == ('crisis_route' if mode == 'crisis' else 'block_input')


def test_total_deadline_fails_closed_and_joins_provider_cancellation(monkeypatch):
    monkeypatch.setattr(m, 'MODERATION_GATE_TIMEOUT', .02)
    cancelled = []
    async def hanging(name):
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.append(name)
    async def oa(*args, **kwargs):
        return await hanging('oa')
    async def age(*args, **kwargs):
        return await hanging('age')
    monkeypatch.setattr(m, 'amoderate_with_openai', oa)
    monkeypatch.setattr(m, 'aclassify_age_appropriate', age)
    verdict = asyncio.run(m.amoderate_input(**input_args()))
    assert verdict.flagged and verdict.category == 'moderation_unavailable'
    assert sorted(cancelled) == ['age', 'oa']
    assert 'trouble replying' in m.moderation_redirect(verdict)


def test_native_request_deadlines_fail_closed(monkeypatch):
    monkeypatch.setattr(m, 'MODERATION_REQUEST_TIMEOUT', .01)
    async def hang(*args, **kwargs):
        await asyncio.Event().wait()
    monkeypatch.setattr(m, '_async_openai_client', lambda: SimpleNamespace(
        moderations=SimpleNamespace(create=hang)))
    monkeypatch.setattr(m, '_age_model', lambda: SimpleNamespace(ainvoke=hang))
    async def run():
        oa, age = await asyncio.gather(m.amoderate_with_openai('hello'),
                                       m.aclassify_age_appropriate('hello', 'middle'))
        assert oa.flagged and oa.category == 'moderation_unavailable'
        assert not age.age_appropriate and age.concern == 'age_classifier_unavailable'
    asyncio.run(run())


def test_provider_clients_disable_hidden_retries_and_bound_requests(monkeypatch):
    options = []
    def client(**kwargs):
        options.append(kwargs)
        return SimpleNamespace(with_structured_output=lambda _: object())
    monkeypatch.setattr(m, 'AsyncOpenAI', client)
    monkeypatch.setattr(m, 'OpenAI', client)
    monkeypatch.setattr(m, 'ChatOpenAI', client)
    monkeypatch.setattr(m, '_oa_client', None)
    monkeypatch.setattr(m, '_oa_async_client', None)
    m._async_openai_client()
    m._openai_client()
    m._age_model()
    assert len(options) == 3
    assert all(o['max_retries'] == 0 and o['timeout'] == m.MODERATION_REQUEST_TIMEOUT for o in options)


def test_kill_during_provider_check_wins_before_output_emission(monkeypatch):
    monkeypatch.setattr(m, 'OUTPUT_CHUNK_BUFFER_CHARS', 40)
    async def oa(text):
        m.kill_agent('async-test-agent')
        return allowed()
    async def age(*args, **kwargs):
        return age_ok()
    monkeypatch.setattr(m, 'amoderate_with_openai', oa)
    monkeypatch.setattr(m, 'aclassify_age_appropriate', age)
    sm = m.StreamingModerator('synthetic-parent', 'Test Kid', 'async-test-agent', 'middle')
    assert asyncio.run(sm.afeed('A friendly sentence about dinosaurs and their fossils.')) == []
    assert sm.state == m.StreamingState.BLOCKED
    assert sm.block_reason.category == 'killed'


def test_output_crisis_below_initial_buffer_preempts_network(monkeypatch):
    monkeypatch.setattr(m, 'OUTPUT_CHUNK_BUFFER_CHARS', 1000)
    async def unexpected(*args, **kwargs):
        pytest.fail('crisis must be detected even below the initial buffer')
    monkeypatch.setattr(m, 'amoderate_with_openai', unexpected)
    sm = m.StreamingModerator('synthetic-parent', 'Test Kid', 'async-test-agent', 'middle')
    assert asyncio.run(sm.afeed('I want to kill myself')) == []
    assert sm.block_reason.severity == 'crisis'
    assert 'grown-up needs to know' in sm.replacement_message()


@pytest.mark.parametrize('buffer', [0, 40, 1000])
def test_final_gate_kept_at_all_existing_buffer_settings(monkeypatch, buffer):
    monkeypatch.setattr(m, 'OUTPUT_CHUNK_BUFFER_CHARS', buffer)
    monkeypatch.setattr(m, 'OUTPUT_RECHECK_EVERY_CHARS', 240)
    calls = []
    async def oa(text):
        calls.append(text)
        return allowed()
    async def age(text, band, **kwargs):
        assert kwargs['direction'] == 'output'
        return age_ok()
    monkeypatch.setattr(m, 'amoderate_with_openai', oa)
    monkeypatch.setattr(m, 'aclassify_age_appropriate', age)
    sm = m.StreamingModerator('synthetic-parent', 'Test Kid', 'async-test-agent', 'middle')
    async def run():
        chunks = await sm.afeed('Hello')
        if buffer:
            assert chunks == []
        chunks += await sm.afinalize()
        assert ''.join(chunks) == 'Hello'
    asyncio.run(run())
    assert calls == ['Hello']


def test_periodic_output_gate_still_blocks_current_chunk(monkeypatch):
    monkeypatch.setattr(m, 'OUTPUT_CHUNK_BUFFER_CHARS', 0)
    monkeypatch.setattr(m, 'OUTPUT_RECHECK_EVERY_CHARS', 10)
    async def oa(text):
        return m._unavailable('block_output')
    async def age(*args, **kwargs):
        return age_ok()
    monkeypatch.setattr(m, 'amoderate_with_openai', oa)
    monkeypatch.setattr(m, 'aclassify_age_appropriate', age)
    sm = m.StreamingModerator('synthetic-parent', 'Test Kid', 'async-test-agent', 'middle')
    async def run():
        assert await sm.afeed('Hello') == ['Hello']
        assert await sm.afeed(' friends!') == []
        assert await sm.afinalize() == []
    asyncio.run(run())
    assert sm.state == m.StreamingState.BLOCKED
    assert 'trouble replying' in sm.replacement_message()


@pytest.mark.parametrize('text', ['I feel sad', 'My goldfish died', 'Kids at school exclude me'])
def test_input_uses_disclosure_rubric_and_output_uses_answer_rubric(monkeypatch, text):
    prompts = []
    async def ainvoke(prompt, config=None):
        prompts.append(prompt)
        # Script the judge: assert plumbing, not production model quality.
        return age_ok()
    monkeypatch.setattr(m, '_age_model', lambda: SimpleNamespace(ainvoke=ainvoke))
    async def oa(text):
        return allowed()
    monkeypatch.setattr(m, 'amoderate_with_openai', oa)
    async def run():
        assert not (await m.amoderate_input(**input_args(text))).flagged
        sm = m.StreamingModerator('synthetic-parent', 'Test Kid', 'async-test-agent', 'middle')
        assert not (await sm._agate_text('That sounds hard. A trusted grown-up can help.')).flagged
    asyncio.run(run())
    assert "CHILD'S INPUT" in prompts[0] and 'Ordinary sadness, grief' in prompts[0]
    assert "ASSISTANT'S OUTPUT" in prompts[1]
    assert all('parental rules' in p and 'untrusted data' in p for p in prompts)


def test_broad_api_flag_cannot_be_overridden_by_input_rubric(monkeypatch):
    async def oa(text):
        return m.ModerationResult(True, 'medium', 'violence', 'flagged', 'block_input')
    async def age(*args, **kwargs):
        return age_ok()
    monkeypatch.setattr(m, 'amoderate_with_openai', oa)
    monkeypatch.setattr(m, 'aclassify_age_appropriate', age)
    verdict = asyncio.run(m.amoderate_input(**input_args()))
    assert verdict.flagged and verdict.category == 'violence'
    assert m.moderation_redirect(verdict) != m.moderation_redirect(m._unavailable())
    assert 'your grown-up will see this chat' not in m.moderation_redirect(verdict)


def test_output_age_rejection_remains_independent_of_clean_broad_check(monkeypatch):
    async def oa(text):
        return allowed()
    async def age(text, band, *, direction, **kwargs):
        return (age_ok() if direction == 'input' else
                m._AgeAppropriateVerdict(age_appropriate=False, confidence=1,
                                        concern='graphic explanation'))
    monkeypatch.setattr(m, 'amoderate_with_openai', oa)
    monkeypatch.setattr(m, 'aclassify_age_appropriate', age)
    async def run():
        assert not (await m.amoderate_input(**input_args('Why do people get hurt?'))).flagged
        sm = m.StreamingModerator('synthetic-parent', 'Test Kid', 'async-test-agent', 'middle')
        verdict = await sm._agate_text('Scripted inappropriate answer')
        assert verdict.flagged and verdict.suggested_action == 'block_output'
        assert verdict.category == 'age_inappropriate:graphic explanation'
    asyncio.run(run())


@pytest.mark.parametrize('phase', ['initial', 'periodic', 'final'])
def test_canceled_output_gate_never_publishes_pending_content(monkeypatch, phase):
    monkeypatch.setattr(m, 'OUTPUT_CHUNK_BUFFER_CHARS', 0 if phase == 'periodic' else 40)
    monkeypatch.setattr(m, 'OUTPUT_RECHECK_EVERY_CHARS', 10)
    async def run():
        entered = asyncio.Event()
        stopped = asyncio.Event()
        async def gate(*args, **kwargs):
            entered.set()
            try:
                await asyncio.Event().wait()
            finally:
                stopped.set()
        sm = m.StreamingModerator('synthetic-parent', 'Test Kid', 'async-test-agent', 'middle')
        monkeypatch.setattr(sm, '_agate_text', gate)
        if phase == 'periodic':
            assert await sm.afeed('Hello') == ['Hello']
            pending = asyncio.create_task(sm.afeed(' unreviewed content'))
            safe_prefix = 'Hello'
        elif phase == 'initial':
            pending = asyncio.create_task(sm.afeed('Unreviewed pending initial output, still awaiting its checks.'))
            safe_prefix = ''
        else:
            assert await sm.afeed('Short pending output') == []
            pending = asyncio.create_task(sm.afinalize())
            safe_prefix = ''
        await asyncio.wait_for(entered.wait(), 1)
        pending.cancel()
        with pytest.raises(asyncio.CancelledError):
            await pending
        assert stopped.is_set()
        assert sm.assembled_output == safe_prefix
    asyncio.run(run())


def test_gate_timing_labels_do_not_include_family_or_text(monkeypatch):
    from app import observability
    observations = []
    monkeypatch.setattr(observability, 'observe', lambda *args, **kw: observations.append((args, kw)))
    async def oa(text):
        return allowed()
    async def age(*args, **kwargs):
        return age_ok()
    monkeypatch.setattr(m, 'amoderate_with_openai', oa)
    monkeypatch.setattr(m, 'aclassify_age_appropriate', age)
    asyncio.run(m.amoderate_input(**input_args()))
    assert len(observations) == 1
    assert observations[0][0][0] == 'moderation.gate.duration_ms'
    assert observations[0][0][1] >= 0
    assert observations[0][1] == {'phase': 'input'}
