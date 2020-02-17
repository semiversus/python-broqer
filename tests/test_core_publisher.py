from unittest import mock

import pytest

from broqer import Publisher, SubscriptionError, Value, NONE, Sink


def test_subscribe():
    """ Testing .subscribe() and .unsubscibe() of Publisher. """
    s1 = Value()
    s2 = Value()

    publisher = Publisher()
    assert len(publisher.subscriptions) == 0

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
    d2.dispose()
    assert len(publisher.subscriptions) == 1
    publisher.unsubscribe(s1)
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
    """ Test .as_future() method """
    publisher = Publisher()

    # test omit_subscription=False when publisher has no state. This should
    # wait for the first state change
    event_loop.call_soon(publisher.notify, 1)
    assert await publisher.as_future(timeout=1, omit_subscription=False) == 1

    # omit_subscription is defaulted to True, so the current state should not
    # be returned, instead it should wait for the first change
    event_loop.call_soon(publisher.notify, 2)
    assert await publisher.as_future(timeout=1) == 2

    # when publisher has a state and omit_subscription is False it should
    # directly return publisher's state
    event_loop.call_soon(publisher.notify, 3)
    assert await publisher.as_future(timeout=1, omit_subscription=False) == 2

    assert (await publisher) == 2


@pytest.mark.parametrize('init', [0, 'Test', {'a':1}, None, (1,2,3), [1,2,3]])
def test_get(init):
    """ Testing .get() method """
    # testing .get() after initialisation
    p1 = Publisher(init)
    p2 = Publisher()
    p3 = Publisher(3)

    assert p1.get() is init
    assert p2.get() is NONE
    assert p3.get() is 3

    # testing .get() after notfiy
    p1.notify(1)
    p2.notify(init)
    p3.notify(init)

    assert p1.get() is 1
    assert p2.get() is init
    assert p3.get() is init


@pytest.mark.parametrize('number_of_subscribers', range(3))
@pytest.mark.parametrize('init', [NONE, 0, 'Test', {'a':1}, None, (1,2,3), [1,2,3]])
def test_notify(init, number_of_subscribers):
    """ Testing .notify(v) method """
    p = Publisher(init)
    m = mock.Mock()

    # subscribing Sinks to the publisher and test .notify on subscribe
    subscribers = [Sink(m, i) for i in range(number_of_subscribers)]

    m.assert_not_called()

    for s in subscribers:
        p.subscribe(s)

    if init is not NONE:
        m.assert_has_calls([mock.call(i, init) for i in range(number_of_subscribers)])
    else:
        m.assert_not_called()

    m.reset_mock()

    # test .notify() for listening subscribers
    p.notify(1)

    m.assert_has_calls([mock.call(i, 1) for i in range(number_of_subscribers)])

    m.reset_mock()

    # re- .notify() with the same value
    p.notify(1)

    m.assert_has_calls([mock.call(i, 1) for i in range(number_of_subscribers)])


def test_subscription_callback():
    """ testing .register_on_subscription_callback() """
    m = mock.Mock()

    p = Publisher()
    p.register_on_subscription_callback(m)

    # callback should be called on first subscription (with True as argument)
    m.assert_not_called()

    d1 = p.subscribe(Sink())
    m.assert_called_once_with(True)
    m.reset_mock()

    # it should not be called until the last subscriber is unsubscribing
    d2 = p.subscribe(Sink())
    d1.dispose()

    m.assert_not_called()

    # callback should be called with False as argument on last unsubscription
    d2.dispose()
    m.assert_called_once_with(False)
    m.reset_mock()

    # callback should again be called with True as argument on first subscription
    p.subscribe(Sink())
    m.assert_called_once_with(True)


def test_prepend():
    """ Testing the prepend argument in .subscribe() """
    m = mock.Mock()
    p = Publisher()

    s1 = Sink(m, 1)
    s2 = Sink(m, 2)
    s3 = Sink(m, 3)
    s4 = Sink(m, 4)

    p.subscribe(s1)
    p.subscribe(s2, prepend=True)  # will be inserted before s1
    p.subscribe(s3)  # will be appended after s1
    p.subscribe(s4, prepend=True)  # will be inserted even before s2

    p.notify('test')

    # notification order should now be: s4, s2, s1, s3
    m.assert_has_calls([mock.call(4, 'test'), mock.call(2, 'test'), mock.call(1, 'test'), mock.call(3, 'test')])


def test_reset_state():
    """ Test .reset_state() """
    m = mock.Mock()
    p = Publisher()

    p.subscribe(Sink(m, 1))

    m.assert_not_called()

    # test .reset_state() before and after subscribing
    p.reset_state('test')
    assert p.get() == 'test'

    p.subscribe(Sink(m, 2))

    m.assert_called_once_with(2, 'test')

    m.reset_mock()

    # test .reset_state() after notify
    p.notify('check')
    assert p.get() == 'check'
    m.assert_has_calls([mock.call(1, 'check'), mock.call(2, 'check')])
    m.reset_mock()

    # test no subscribers get notified
    p.reset_state('test')
    m.assert_not_called()

    assert p.get() == 'test'

    # test default argument NONE for .reset_state()
    p.reset_state()
    m.assert_not_called()

    assert p.get() == NONE