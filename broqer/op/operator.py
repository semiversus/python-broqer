""" Module implementing Operator, MultiOperator and build_operator.
"""
from abc import abstractmethod

from broqer import Publisher, Subscriber, SubscriptionDisposable


class Operator(Publisher, Subscriber):  # pylint: disable=abstract-method
    """ Base class for operators depending on a single publisher. This
    publisher will be subscribed as soon as this operator is subscribed the
    first time.

    On unsubscription of the last subscriber the dependent publisher will also
    be unsubscripted.
    """
    def __init__(self, publisher: Publisher) -> None:
        Publisher.__init__(self)
        Subscriber.__init__(self)
        self._publisher = publisher

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
                subscriber.emit(value, who=self)  # pylint: disable=E1133
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
    def get(self):  # pylint: disable=useless-return, no-self-use
        """ Get value of operator """


class MultiOperator(Publisher, Subscriber):  # pylint: disable=abstract-method
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
                subscriber.emit(value, who=self)  # pylint: disable=E1133
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
    def get(self):  # pylint: disable=useless-return, no-self-use
        """ Get value of operator """


def build_operator(operator_cls):
    """ This function is taking an operator class and is returning a function
    to be called when used in a pipeline. _op function is a closure to add
    arguments to the class initialisation.

    The resulting function takes a publisher as argument and returns a new
    publisher corresponding the operator functionality.
    """
    def _op(*args, **kwargs):
        def _build(publisher):
            return operator_cls(publisher, *args, **kwargs)
        return _build
    return _op
