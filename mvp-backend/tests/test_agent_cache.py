from concurrent.futures import ThreadPoolExecutor

import pytest

from app.agent_runtime.cache import AgentCache


def test_lru_evicts_graph_only_and_keeps_hot_tenant():
    cache = AgentCache(maxsize=2)
    cache['a'] = {'agent': 'a graph', 'context': 'a profile'}
    cache['b'] = {'agent': 'b graph', 'context': 'b profile'}
    assert cache.get('a')['agent'] == 'a graph'
    cache['c'] = {'agent': 'c graph', 'context': 'c profile'}
    assert list(cache) == ['a', 'c']
    assert cache.get('b') is None
    assert cache.pop('a')['context'] == 'a profile'
    cache.clear()
    assert len(cache) == 0


def test_concurrent_cache_access_stays_bounded_and_tenant_scoped():
    cache = AgentCache(maxsize=12)
    def put(i):
        cache[f'user-{i}'] = {'tenant': i}
        value = cache.get(f'user-{i}')
        assert value is None or value['tenant'] == i
        list(cache.keys())
    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(put, range(100)))
    assert len(cache) == 12


@pytest.mark.parametrize('size', [0, -1])
def test_cache_rejects_unbounded_or_disabled_sizes(size):
    with pytest.raises(ValueError):
        AgentCache(maxsize=size)
