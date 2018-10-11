import asyncio
from unittest import mock
import pytest

from broqer import Hub, op, Value, Subject, SubHub, StatefulPublisher
from broqer.hub import Topic, MetaTopic

def test_hub_topics():
    hub = Hub()

    # test __getitem__
    t = hub['value1']
    assert t is hub['value1']

    hub['value2']

    with pytest.raises(TypeError):
        hub['value3'] = 0

    # test __contains__
    assert 'value1' in hub
    assert 'value2' in hub
    assert 'value3' not in hub

    # test __iter__
    assert ('value1', 'value2') == tuple(t for t in hub)

    # test .topics property
    assert 'value1' in hub.topics
    assert 'value2' in hub.topics
    assert 'value3' not in hub.topics

    assert ('value1', 'value2') == tuple(hub.topics)

def test_freeze():
    hub = Hub()

    hub['value1'].assign(StatefulPublisher(0))

    assert 'value1' in hub

    hub.freeze()

    assert len(tuple(hub)) == 1

    hub.freeze(False)

    hub['value2'] | op.Sink()
    hub['value3'].emit(1)

    assert 'value2' in hub
    assert 'value3' in hub

    with pytest.raises(ValueError):
        hub.freeze()

    hub['value2'].assign(Value(0))
    hub['value3'].assign(Value(0))

    hub.freeze()

    with pytest.raises(ValueError):
        hub['value4'].assign(StatefulPublisher(0))

    with pytest.raises(ValueError):
        hub['value5'] | op.Sink()

    with pytest.raises(ValueError):
        hub['value6'].emit(1)

    assert len(tuple(hub)) == 3

    hub.freeze(False)

    hub['value4'] | op.Sink()
    hub['value5'].assign(StatefulPublisher(0))
    hub['value6'].emit(1)

    assert 'value4' in hub
    assert 'value5' in hub
    assert 'value6' in hub

    assert len(tuple(hub)) == 6

@pytest.mark.parametrize('factory', [Topic, MetaTopic])
def test_assign_subscribe_emit(factory):
    hub = Hub(topic_factory=factory)

    # assign, subscribe and emit
    value1 = Value(0)
    assert not hub['value1'].assigned
    assert hub['value1'].subject is None

    hub['value1'].assign(value1)

    with pytest.raises(ValueError):
        hub['value1'].assign(value1)

    assert hub['value1'].path == 'value1'
    assert hub['value1'].assigned
    assert 'value1' in hub
    assert hub['value1'] is not value1
    assert hub['value1'].subject is value1


    assert len(value1._subscriptions) == 0
    assert len(hub['value1']._subscriptions) == 0

    value2 = Subject()
    hub['value2'].assign(value2)

    mock_sink1 = mock.Mock()
    mock_sink2 = mock.Mock()

    dispose_value1 = hub['value1'] | op.Sink(mock_sink1)
    dispose_value2 = hub['value2'] | op.Sink(mock_sink2)

    assert len(value1._subscriptions) == 1
    assert len(hub['value1']._subscriptions) == 1
    mock_sink1.assert_called_once_with(0)

    assert len(value1._subscriptions) == 1
    assert len(hub['value1']._subscriptions) == 1
    mock_sink2.assert_not_called()

    mock_sink1.reset_mock()
    mock_sink2.reset_mock()
    hub['value1'].emit(1)
    hub['value2'].emit(1)
    mock_sink1.assert_called_once_with(1)
    mock_sink2.assert_called_once_with(1)
    assert value1.get() == 1

    mock_sink1b = mock.Mock()
    dispose_value1b = hub['value1'] | op.Sink(mock_sink1b)
    mock_sink1b.assert_called_once_with(1)

    dispose_value1.dispose()
    dispose_value1b.dispose()

    mock_sink2b = mock.Mock()
    hub['value2'] | op.Sink(mock_sink2b)
    mock_sink2b.assert_not_called()

    assert len(value1._subscriptions) == 0
    assert len(hub['value1']._subscriptions) == 0

    with pytest.raises(ValueError):
        hub['value3'].get()

@pytest.mark.parametrize('factory', [Topic, MetaTopic])
def test_subscribe_emit_assign(factory):
    hub = Hub(topic_factory=factory)

    mock_sink = mock.Mock()
    mock_sink2 = mock.Mock()

    disposable = hub['value1'] | op.Sink(mock_sink)

    mock_sink.assert_not_called()

    assert len(hub['value1']._subscriptions) == 1

    hub['value1'].emit(1)
    hub['value1'].emit(2)

    mock_sink.assert_not_called()

    disposable.dispose()

    assert len(hub['value1']._subscriptions) == 0

    hub['value1'] | op.Sink(mock_sink)
    hub['value1'] | op.Sink(mock_sink2)

    value = Value(0)

    hub['value1'].assign(value)
    mock_sink.calls(mock.call(0), mock.call(1), mock.call(2))

def test_meta_topic():
    hub = Hub(topic_factory=MetaTopic)
    assert hub['value1'].meta == dict()

    with pytest.raises(AttributeError):
        hub['value1'].meta = dict()

    hub['value1'].meta.update({'a':1, 'b':2})
    assert hub['value1'].meta == {'a':1, 'b':2}

    hub['value1'].meta['b'] = 3

    hub['value1'].assign(Value(0), meta={'b':4, 'c':3})
    assert hub['value1'].meta == {'a':1, 'b':4, 'c':3}

def test_sub_hub():
    hub = Hub()

    hub['value1'].assign(Value(0))
    hub['prefix.value2'].assign(Value(1))

    sub_hub = SubHub(hub, 'prefix')
    assert sub_hub['value2'] is hub['prefix.value2']

    sub_hub['value3'].assign(Value(3))

    assert hub['prefix.value3'] is sub_hub['value3']
    assert sub_hub.prefix == 'prefix'