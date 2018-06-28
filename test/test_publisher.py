from unittest import mock

import pytest

from broqer import Publisher, SubscriptionError
from broqer.subject import Subject


@pytest.mark.parametrize('cls', [Publisher])
def test_subscribe(cls):
    s1 = Subject()
    s2 = Subject()

    publisher = cls()
    assert len(publisher) == 0

    # subscribe first subscriber
    d1 = publisher.subscribe(s1)
    assert s1 in publisher
    assert s2 not in publisher
    assert len(publisher) == 1

    # re - subscribe should fail
    with pytest.raises(SubscriptionError):
        publisher.subscribe(s1)

    # subscribe second subscriber
    d2 = publisher.subscribe(s2)
    assert len(publisher) == 2
    assert s1 in publisher
    assert s2 in publisher

    # unsubscribe both subscribers
    d1.dispose()
    assert len(publisher) == 1
    publisher.unsubscribe(s2)
    assert len(publisher) == 0

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
