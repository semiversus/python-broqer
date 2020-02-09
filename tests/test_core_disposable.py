from broqer import SubscriptionDisposable, Publisher, Value


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



