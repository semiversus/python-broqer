""" Module implementing Operator, MultiOperator.
"""
import asyncio
from abc import abstractmethod
from functools import reduce
from operator import or_
from typing import Any

from broqer.publisher import Publisher
from broqer.disposable import SubscriptionDisposable
from broqer.subscriber import Subscriber


class _EmitSink(Subscriber):  # pylint: disable=too-few-public-methods
    def __init__(self, operator):
        self._operator = operator

    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        return self._operator.emit_op(value, who=who)


class Operator(Publisher):
    """ Base class for operators depending on a single publisher. This
    publisher will be subscribed as soon as this operator is subscribed the
    first time.

    On unsubscription of the last subscriber the dependent publisher will also
    be unsubscripted.
    """
    def __init__(self) -> None:
        Publisher.__init__(self)
        self._emit_sink = _EmitSink(self)
        self._publisher = None  # type: Publisher

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)

        if len(self._subscriptions) == 1:  # if this was the first subscription
            self._publisher.subscribe(self._emit_sink)

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._publisher.unsubscribe(self._emit_sink)

    @property
    def source_publishers(self):
        """ Tuple with all source publishers """
        return (self._publisher, )

    @abstractmethod
    def emit_op(self, value: Any, who: Publisher) -> None:
        """ Send new value to the operator
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """

    def apply(self, publisher: Publisher) -> Publisher:
        if self._publisher is not None:
            raise ValueError('Operator can only be connected to one publisher')

        self._publisher = publisher
        return self

    def __ror__(self, publisher: Publisher) -> Publisher:
        return self.apply(publisher)


class MultiOperator(Publisher):
    """ Base class for operators depending on multiple publishers. Like
    Operator all publishers will be subscribed on first subscription to this
    operator. Accordingly all publishers get unsubscribed on unsubscription
    of the last subscriber.
    """
    def __init__(self, *publishers: Publisher) -> None:
        Publisher.__init__(self)
        self._emit_sink = _EmitSink(self)
        self._publishers = publishers

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)

        if len(self._subscriptions) == 1:  # if this was the first subscription
            for _publisher in self._publishers:
                # subscribe to all dependent publishers
                _publisher.subscribe(self._emit_sink)

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions:
            for _publisher in self._publishers:
                _publisher.unsubscribe(self._emit_sink)

    @property
    def source_publishers(self):
        """ Tuple with all source publishers """
        return self._publishers

    @abstractmethod
    def emit_op(self, value: Any, who: Publisher) -> None:
        """ Send new value to the operator
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """


class OperatorConcat(Operator):
    """ This class is generator a new operator by concatenation of other
    operators.

    :param operators: the operators to concatenate
    """
    def __init__(self, *operators):
        Operator.__init__(self)
        self._operators = operators

    def emit_op(self, value: Any, who: Publisher) -> None:
        return self.notify(value)

    def apply(self, publisher: Publisher) -> Publisher:
        Operator.apply(self, publisher)

        # concat each operator in the following step
        reduce(or_, self._operators, publisher)

        # the source publisher is the last operator in the chain
        self._publisher = self._operators[-1]
        return self
