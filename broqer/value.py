""" Implementing Value """

from typing import Any

# pylint: disable=cyclic-import
from broqer import Publisher, NONE
from broqer.operator import Operator


class Value(Operator):
    """
    Value is a publisher and subscriber.

    >>> from broqer import Sink

    >>> s = Value(0)
    >>> _d = s.subscribe(Sink(print))
    0
    >>> s.emit(1)
    1
    """
    def __init__(self, init=NONE):
        Operator.__init__(self)
        self._state = init

    def emit(self, value: Any,
             who: Publisher = None) -> None:  # pylint: disable=unused-argument
        if self._originator is not None and self._originator is not who:
            raise ValueError('Emit from non assigned publisher')

        return Publisher.notify(self, value)


def dependent_subscribe(publisher: Publisher, value: Value):
    """ Let `value` subscribe to `publisher` only when `value` itself is subscribed
    :param publisher: publisher to be subscribed, when value is subscribed
    :param value: value, which will receive .emit calls from `publisher`
    """
    def _on_subscription(existing_subscription: bool):
        if existing_subscription:
            publisher.subscribe(value)
        else:
            publisher.unsubscribe(value)

    value.register_on_subscription_callback(_on_subscription)