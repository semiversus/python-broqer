from unittest import mock

from broqer import Disposable, SubscriptionDisposable, Publisher, Value


def test_disposable():
    """ Testing base class Disposable
    """
    m = mock.Mock()

    class MyDisposable(Disposable):
        def dispose(self):
            m('disposed')

    d = MyDisposable()

    # test simple .dispose() call
    m.assert_not_called()
    d.dispose()
    m.assert_called_once_with('disposed')

    m.reset_mock()

    # test context manager
    with d:
        m.assert_not_called()

    m.assert_called_once_with('disposed')

    m.reset_mock()

    # test context manager creating the disposable
    with MyDisposable() as d2:
        m.assert_not_called()

    m.assert_called_once_with('disposed')


def test_subscription_disposable():
    p = Publisher()
    v = Value(0)

    assert len(p.subscriptions) == 0

    disposable = p.subscribe(v)

    assert len(p.subscriptions) == 1

    assert disposable.publisher is p
    assert disposable.subscriber is v

    disposable.dispose()

    assert len(p.subscriptions) == 0

    with p.subscribe(v):
        assert len(p.subscriptions) == 1

    assert len(p.subscriptions) == 0



