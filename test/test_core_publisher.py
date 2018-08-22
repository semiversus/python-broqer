from unittest import mock
import asyncio

import pytest

from broqer import Publisher, SubscriptionError, Subscriber, Value, StatefulPublisher, op
from broqer.subject import Subject


@pytest.mark.parametrize('cls', [Publisher])
def test_subscribe(cls):
    s1 = Subject()
    s2 = Subject()

    publisher = cls()
    assert len(publisher.subscriptions) == 0

    with pytest.raises(ValueError):
        publisher.get()

    # subscribe first subscriber
    d1 = publisher.subscribe(s1)
    assert s1 in publisher.subscriptions
    # assert s2 not in publisher.subscriptions
    assert len(publisher.subscriptions) == 1

    # re - subscribe should fail
    with pytest.raises(SubscriptionError):
        publisher.subscribe(s1)

    # subscribe second subscriber
    d2 = publisher.subscribe(s2)
    assert len(publisher.subscriptions) == 2
    assert s1 in publisher.subscriptions
    assert s2 in publisher.subscriptions

    # unsubscribe both subscribers
    d1.dispose()
    assert len(publisher.subscriptions) == 1
    publisher.unsubscribe(s2)
    assert len(publisher.subscriptions) == 0

    # re - unsubscribing should fail
    with pytest.raises(SubscriptionError):
        d1.dispose()

    with pytest.raises(SubscriptionError):
        publisher.unsubscribe(s1)

    with pytest.raises(SubscriptionError):
        d2.dispose()


@pytest.mark.parametrize('cls', [Publisher])
def test_chaining_operator(cls):
    publisher = cls()

    build_cb = mock.Mock()
    publisher | build_cb

    build_cb.assert_called_with(publisher)


@pytest.mark.asyncio
@pytest.mark.parametrize('cls', [Publisher])
async def test_await(cls, event_loop):
    publisher = cls()

    event_loop.call_soon(publisher.notify, 1)
    assert await publisher == 1

    event_loop.call_soon(publisher.notify, 2)
    assert await publisher.to_future() == 2

@pytest.mark.asyncio
async def test_future_return():
    class S(Subscriber):
        def __init__(self):
            self.future = asyncio.get_event_loop().create_future()

        def emit(self, value, who: Publisher) -> asyncio.Future:
            return self.future
    
    p = Publisher()
    s1 = S()

    p.subscribe(s1)

    assert p.notify(None) is s1.future

    s2 = S()

    p.subscribe(s2)

    gathered_future = p.notify(None)

    await asyncio.sleep(0)
    assert not gathered_future.done()

    s1.future.set_result(1)
    await asyncio.sleep(0)
    assert not gathered_future.done()

    s2.future.set_result(1)
    await asyncio.sleep(0)
    assert gathered_future.done()

def test_stateful_publisher():
    p = StatefulPublisher()
    v = Value(0)

    with pytest.raises(ValueError):
        p.get()

    mock_sink = mock.Mock()

    disposable = p | v
    v | op.sink(mock_sink)

    mock_sink.assert_called_once_with(0)
    mock_sink.reset_mock()

    p.notify(1)

    mock_sink.assert_called_once_with(1)
    assert p.get() == 1
    mock_sink.reset_mock()

    p.notify(1)
    assert p.get() == 1
    mock_sink.assert_not_called()

    p.notify(2)
    assert p.get() == 2
    mock_sink.assert_called_once_with(2)

    p.reset_state()

    with pytest.raises(ValueError):
        p.get()

    p.reset_state(3)
    assert p.get() == 3
