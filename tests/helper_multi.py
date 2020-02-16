from unittest import mock

import pytest

from broqer import Publisher, NONE, Sink


def check_get_method(operator, input_vector, output_vector):
    input_value, output_value = input_vector[0], output_vector[0]

    publishers = operator.dependencies

    for p, v in zip(publishers, input_value):
            p.get = mock.MagicMock(return_value=v)

    with pytest.raises(ValueError):
        operator.emit(input_value[0], who=None)

    assert operator.get() == output_value

    disposable = operator.subscribe(Sink())

    for p, v in zip(publishers, input_value):
        if v is not NONE:
            operator.emit(v, who=p)  # simulate emit on subscribe

    for p, v in zip(publishers, input_value):
        p.get = None  # .get should not be called when operator has a subscription

    assert operator.get() == output_value  # this should retrieve the internal state

    # after unsubscription it should remove the internal state and retrieve it
    # directly from orignator publisher via get
    disposable.dispose()

    for p, v in zip(publishers, input_value):
        p.get = mock.MagicMock(return_value=v)

    assert operator.get() == output_value

    for p in publishers:
        p.get.assert_called_once_with()


def check_subscription(operator, input_vector, output_vector):
    m = mock.Mock()

    publishers = operator.dependencies

    # subscribe operator to publisher
    disposable = operator.subscribe(Sink(m))

    for p in publishers:
        assert p.subscriptions == (operator,)  # now it should be subscribed

    assert operator.dependencies == publishers

    # test emit on subscription
    if output_vector[0] is not NONE:
        m.assert_called_once_with(output_vector[0])

    m.reset_mock()

    # test input_vector
    for input_value, output_value in zip(input_vector[1:], output_vector[1:]):
        for p, v in zip(publishers, input_value):
            if v is not NONE:
                p.notify(v)

        if output_value is NONE:
            m.assert_not_called()
        else:
            m.assert_called_with(output_value)
        m.reset_mock()

    # test input_vector with unsubscriptions between
    disposable.dispose()

    assert operator.dependencies == publishers

    for p, v in zip(publishers, input_vector[0]):
        p.notify(v)

    disposable = operator.subscribe(Sink(m))

    for input_value, output_value in zip(input_vector, output_vector):
        m.reset_mock()

        for p, v in zip(publishers, input_value):
            if v is not NONE:
                p.notify(v)

        if output_value is NONE:
            m.assert_not_called()
        else:
            m.assert_called_with(output_value)


def check_dependencies(operator, *_):
    publishers = operator.dependencies

    for p in publishers:
        assert p.subscriptions == ()  # operator should not be subscribed yet

    assert operator.subscriptions == ()

    # subscribe to operator
    disposable1 = operator.subscribe(Sink())

    assert p.subscriptions == (operator,)  # operator should now be subscriped
    assert operator.subscriptions == (disposable1.subscriber,)

    # second subscribe to operator
    disposable2 = operator.subscribe(Sink(), prepend=True)

    assert p.subscriptions == (operator,)
    assert operator.subscriptions == (disposable2.subscriber, disposable1.subscriber)

    # remove first subscriber
    disposable1.dispose()

    assert p.subscriptions == (operator,)
    assert operator.subscriptions == (disposable2.subscriber,)

    # remove second subscriber
    disposable2.dispose()

    assert p.subscriptions == ()  # operator should now be subscriped
    assert operator.subscriptions == ()

