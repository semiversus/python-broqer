from unittest import mock

import pytest

from broqer import Publisher, NONE, op, Sink


def check_get_method(operator, input_vector, output_vector):
    input_value, output_value = input_vector[0], output_vector[0]

    p = Publisher()
    p.get = mock.MagicMock(return_value=input_value)
    o = p | operator

    with pytest.raises(ValueError):
        o.emit(input_value, who=None)

    assert o.get() == output_value

    disposable = o.subscribe(Sink())

    if input_value is not NONE:
        o.emit(input_value, who=p)  # simulate emit on subscribe

    p.get = None  # .get should not be called when operator has a subscription

    assert o.get() == output_value  # this should retrieve the internal state

    # after unsubscription it should remove the internal state and retrieve it
    # directly from orignator publisher via get
    disposable.dispose()

    p.get = mock.MagicMock(return_value=input_value)

    assert o.get() == output_value

    p.get.assert_called_once_with()


def check_subscription(operator, input_vector, output_vector):
    assert len(input_vector) == len(output_vector)

    m = mock.Mock()

    p = Publisher(input_vector[0])
    o = p | operator

    o2 = Publisher() | operator

    # subscribe operator to publisher
    disposable = o.subscribe(Sink(m))

    assert p.subscriptions == (o,)  # now it should be subscribed
    assert o.dependencies == (p,)

    # test emit on subscription
    if output_vector[0] is not NONE:
        m.assert_called_once_with(output_vector[0])

    m.reset_mock()

    # test input_vector
    for input_value, output_value in zip(input_vector[1:], output_vector[1:]):
        if input_value is not NONE:
            p.notify(input_value)

        if output_value is NONE:
            m.assert_not_called()
        else:
            m.assert_called_with(output_value)
        m.reset_mock()

    # test input_vector with unsubscriptions between
    disposable.dispose()
    assert o.dependencies == (p,)
    disposable = o.subscribe(Sink(m))

    for input_value, output_value in zip(input_vector, output_vector):
        if input_value is not NONE:
            m.reset_mock()
            p.notify(input_value)
            if output_value is NONE:
                m.assert_not_called()
            else:
                m.assert_called_once_with(output_value)


def check_dependencies(operator, *_):
    p = Publisher(NONE)

    assert len(p.subscriptions) == 0

    o = p | operator

    assert p.subscriptions == ()  # operator should not be subscribed yet
    assert o.dependencies == (p,)
    assert o.subscriptions == ()

    # subscribe to operator
    disposable1 = o.subscribe(Sink())

    assert p.subscriptions == (o,)  # operator should now be subscriped
    assert o.dependencies == (p,)
    assert o.subscriptions == (disposable1.subscriber,)

    # second subscribe to operator
    disposable2 = o.subscribe(Sink(), prepend=True)

    assert p.subscriptions == (o,)
    assert o.dependencies == (p,)
    assert o.subscriptions == (disposable2.subscriber, disposable1.subscriber)

    # remove first subscriber
    disposable1.dispose()

    assert p.subscriptions == (o,)
    assert o.dependencies == (p,)
    assert o.subscriptions == (disposable2.subscriber,)

    # remove second subscriber
    disposable2.dispose()

    assert p.subscriptions == ()  # operator should now be subscriped
    assert o.dependencies == (p,)
    assert o.subscriptions == ()

