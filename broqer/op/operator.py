""" Module implementing Operator, MultiOperator.
"""
import typing
from abc import abstractmethod

from broqer import NONE, Publisher, SubscriptionDisposable, Subscriber
from broqer.publisher import TValue, TValueNONE


class Operator(Publisher, Subscriber):
    """ Base class for operators depending on a single publisher. This
    publisher will be subscribed as soon as this operator is subscribed the
    first time.

    On unsubscription of the last subscriber the dependent publisher will also
    be unsubscripted.
    """
    def __init__(self) -> None:
        Publisher.__init__(self)
        Subscriber.__init__(self)
        self._orginator = None  # type: typing.Optional[Publisher]

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        assert isinstance(self._orginator, Publisher)

        disposable = Publisher.subscribe(self, subscriber, prepend)

        if len(self._subscriptions) == 1:  # if this was the first subscription
            self._orginator.subscribe(self)

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        assert isinstance(self._orginator, Publisher)

        Publisher.unsubscribe(self, subscriber)

        if not self._subscriptions:
            self._orginator.unsubscribe(self)
            Publisher.reset_state(self)

    def apply(self, publisher: Publisher) -> Publisher:
        """ Apply the operator to a publisher """
        if self._orginator is not None:
            raise ValueError('Operator can only be connected to one publisher')

        self._orginator = publisher
        self.add_dependencies(self._orginator)

        return self

    def notify(self, value: TValue) -> None:
        raise ValueError('Operator doesn\'t support .notify()')

    def reset_state(self, value: TValueNONE = NONE) -> None:
        raise ValueError('Operator doesn\'t support .reset_state()')

    def __ror__(self, publisher: Publisher) -> Publisher:
        return self.apply(publisher)

    @abstractmethod
    def emit(self, value: typing.Any, who: Publisher) -> None:
        """ Send new value to the operator
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """


class MultiOperator(Publisher, Subscriber):
    """ Base class for operators depending on multiple publishers. Like
    Operator all publishers will be subscribed on first subscription to this
    operator. Accordingly all publishers get unsubscribed on unsubscription
    of the last subscriber.
    """
    def __init__(self, *publishers: Publisher) -> None:
        Publisher.__init__(self)
        Subscriber.__init__(self)
        self._orginators = publishers
        self.add_dependencies(*publishers)

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)

        if len(self._subscriptions) == 1:  # if this was the first subscription
            for publisher in self._orginators:
                # subscribe to all dependent publishers
                publisher.subscribe(self)

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions:
            for publisher in self._orginators:
                publisher.unsubscribe(self)
            Publisher.reset_state(self)

    def notify(self, value: TValue) -> None:
        raise ValueError('Operator doesn\'t support .notify()')

    def reset_state(self, value: TValueNONE = NONE) -> None:
        raise ValueError('Operator doesn\'t support .reset_state()')

    @abstractmethod
    def emit(self, value: typing.Any, who: Publisher) -> None:
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

    def emit(self, value: typing.Any, who: Publisher) -> None:
        return Publisher.notify(self, value)

    def apply(self, publisher: Publisher) -> Publisher:
        # concat each operator in the following step
        orginator = publisher

        for operator in self._operators:
            operator.apply(orginator)
            orginator = operator

        # the source publisher is the last operator in the chain
        Operator.apply(self, self._operators[-1])

        return self._operators[-1]
