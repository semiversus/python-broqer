from unittest import mock
import asyncio

import pytest

from broqer import Publisher, SubscriptionError, Subscriber, Value, op, NONE


def test_subscribe():
    s1 = Value()
    s2 = Value()

    publisher = Publisher()
    assert len(publisher.subscriptions) == 0

    assert publisher.get() is NONE

    # subscribe first subscriber
    d1 = publisher.subscribe(s1)
    assert any(s1 is s for s in publisher.subscriptions)
    assert not any(s2 is s for s in publisher.subscriptions)
    assert len(publisher.subscriptions) == 1

    # re - subscribe should fail
    with pytest.raises(SubscriptionError):
        publisher.subscribe(s1)

    # subscribe second subscriber
    d2 = publisher.subscribe(s2)
    assert len(publisher.subscriptions) == 2
    assert any(s1 is s for s in publisher.subscriptions)
    assert any(s2 is s for s in publisher.subscriptions)

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


@pytest.mark.asyncio
async def test_await(event_loop):
    publisher = Publisher()

    event_loop.call_soon(publisher.notify, 1)
    assert (await publisher) == 1

    event_loop.call_soon(publisher.notify, 2)
    assert await publisher.wait_for() == 2

def test_stateful_publisher():
    p = Publisher(0)
    v = Value()

    assert p.get() is 0
    assert v.get() is NONE

    mock_sink = mock.Mock()

    disposable = p.subscribe(v)
    v.subscribe(op.Sink(mock_sink))

    mock_sink.assert_called_once_with(0)
    mock_sink.reset_mock()

    p.notify(1)

    mock_sink.assert_called_once_with(1)
    assert p.get() == 1
    mock_sink.reset_mock()

    p.notify(1)

    mock_sink.assert_called_once_with(1)
    assert p.get() == 1
    mock_sink.reset_mock()

    p.notify(2)
    assert p.get() == 2
    mock_sink.assert_called_once_with(2)
