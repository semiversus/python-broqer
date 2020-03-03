""" Module implementing Operator, MultiOperator.
"""
import typing
from abc import abstractmethod, ABCMeta

# pylint: disable=cyclic-import
from broqer import Publisher, SubscriptionDisposable, Subscriber
from broqer.publisher import TValue


class OperatorMeta(ABCMeta):
    """ Metaclass for operators. Defining __ror__ for operator classes.
    This is e.g. used for EvalTrue: p | EvalTrue is equal to EvalTrue(p)
    """
    def __ror__(cls, publisher: Publisher) -> Publisher:
        return cls(publisher)  # pylint: disable=no-value-for-parameter


class Operator(Publisher, Subscriber, metaclass=OperatorMeta):
    """ Base class for operators depending on a single publisher. This
    publisher will be subscribed as soon as this operator is subscribed the
    first time.

    On unsubscription of the last subscriber the dependent publisher will also
    be unsubscripted.
    """
    def __init__(self, publisher: Publisher) -> None:
        Publisher.__init__(self)
        Subscriber.__init__(self)
        self._orginator = publisher
        self.add_dependencies(publisher)

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)

        if len(self._subscriptions) == 1:  # if this was the first subscription
            self._orginator.subscribe(self)

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)

        if not self._subscriptions:
            self._orginator.unsubscribe(self)
            Publisher.reset_state(self)

    def notify(self, value: TValue) -> None:
        raise ValueError('Operator doesn\'t support .notify()')

    def reset_state(self, value: TValue = None) -> None:
        raise ValueError('Operator doesn\'t support .reset_state()')

    @abstractmethod
    def emit(self, value: typing.Any, who: Publisher) -> None:
        """ Send new value to the operator
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """


class OperatorFactory:
    """ OperatorFactory is returning operator objects applied to a publisher
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def apply(self, publisher: Publisher) -> Publisher:
        """ Build a operator applied to the given publisher """

    def __ror__(self, publisher: Publisher) -> Publisher:
        return self.apply(publisher)


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

    def reset_state(self, value: TValue = None) -> None:
        raise ValueError('Operator doesn\'t support .reset_state()')

    @abstractmethod
    def emit(self, value: typing.Any, who: Publisher) -> None:
        """ Send new value to the operator
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """
