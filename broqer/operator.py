""" Module implementing Operator, MultiOperator.
"""
import typing
from abc import abstractmethod

# pylint: disable=cyclic-import
from broqer import Publisher, SubscriptionDisposable, Subscriber
from broqer.publisher import TValue


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
        self._originator = None  # type: typing.Optional[Publisher]

    @property
    def originator(self):
        """ Property returning originator publisher """
        return self._originator

    @originator.setter
    def originator(self, publisher: Publisher):
        """ Setter for originator """
        if self._originator is not None:
            raise TypeError('Operator already assigned to originator')

        self._originator = publisher
        self.add_dependencies(publisher)
        if self._subscriptions:
            self._originator.subscribe(self)

    def __ror__(self, publisher: Publisher) -> Publisher:
        if self._originator is not None:
            raise TypeError('operator already applied')
        self.originator = publisher
        return self

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)

        if len(self._subscriptions) == 1 and self._originator is not None:
            # if this was the first subscription
            self._originator.subscribe(self)

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)

        if not self._subscriptions and self._originator is not None:
            self._originator.unsubscribe(self)
            Publisher.reset_state(self)

    def notify(self, value: TValue) -> None:
        raise ValueError('Operator doesn\'t support .notify()')

    @abstractmethod
    def emit(self, value: typing.Any, who: Publisher) -> None:
        """ Send new value to the operator
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """


class ClassOperatorMeta(type):
    """ Metaclass to be used, when class can directly be used as operator
        e.g. EvalTrue """
    def __ror__(cls, publisher: Publisher):
        return cls(publisher)


class MultiOperator(Publisher, Subscriber):
    """ Base class for operators depending on multiple publishers. Like
    Operator all publishers will be subscribed on first subscription to this
    operator. Accordingly all publishers get unsubscribed on unsubscription
    of the last subscriber.
    """
    def __init__(self, *publishers: Publisher) -> None:
        Publisher.__init__(self)
        Subscriber.__init__(self)
        self._originators = publishers
        self.add_dependencies(*publishers)

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)

        if len(self._subscriptions) == 1:  # if this was the first subscription
            for publisher in self._originators:
                # subscribe to all dependent publishers
                publisher.subscribe(self)

        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions:
            for publisher in self._originators:
                publisher.unsubscribe(self)
            Publisher.reset_state(self)

    def notify(self, value: TValue) -> None:
        raise ValueError('Operator doesn\'t support .notify()')

    def emit(self, value: typing.Any, who: Publisher) -> None:
        """ Send new value to the operator
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """
        raise NotImplementedError('.emit not implemented')
