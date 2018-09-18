""" Module implementing Operator, MultiOperator.
"""
from abc import abstractmethod

from broqer import Publisher, Subscriber, SubscriptionDisposable


class Operator(Subscriber, Publisher):
    """ Base class for operators depending on a single publisher. This
    publisher will be subscribed as soon as this operator is subscribed the
    first time.

    On unsubscription of the last subscriber the dependent publisher will also
    be unsubscripted.
    """
    def __init__(self) -> None:
        Publisher.__init__(self)
        Subscriber.__init__(self)
        self._publisher = None  # type: Publisher

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)
        if len(self._subscriptions) == 1:  # if this was the first subscription
            self._publisher.subscribe(self)
        else:
            try:
                value = self.get()
            except ValueError:
                pass
            else:
                subscriber.emit(value, who=self)
        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._publisher.unsubscribe(self)

    @property
    def source_publishers(self):
        """ Tuple with all source publishers """
        return (self._publisher, )

    @abstractmethod
    def get(self):
        """ Get value of operator """

    def __ror__(self, publisher: Publisher) -> Publisher:
        assert self._publisher is None, \
            'Operator can only be connected to one publisher'
        self._publisher = publisher
        return self


class MultiOperator(Publisher, Subscriber):
    """ Base class for operators depending on multiple publishers. Like
    Operator all publishers will be subscribed on first subscription to this
    operator. Accordingly all publishers get unsubscribed on unsubscription
    of the last subscriber.
    """
    def __init__(self, *publishers: Publisher) -> None:
        Publisher.__init__(self)
        Subscriber.__init__(self)
        self._publishers = publishers

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)
        if len(self._subscriptions) == 1:  # if this was the first subscription
            for _publisher in self._publishers:
                # subscribe to all dependent publishers
                _publisher.subscribe(self)
        else:
            try:
                value = self.get()
            except ValueError:
                pass
            else:
                subscriber.emit(value, who=self)
        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions:
            for _publisher in self._publishers:
                _publisher.unsubscribe(self)

    @property
    def source_publishers(self):
        """ Tuple with all source publishers """
        return self._publishers

    @abstractmethod
    def get(self):
        """ Get value of operator """

    def __ror__(self, publisher: Publisher) -> Publisher:
        self._publishers = (publisher, *self._publishers)
        return self
