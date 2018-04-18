from broqer import Publisher, Subscriber, SubscriptionDisposable


class Operator(Publisher, Subscriber):
    """ Base class for operators depending on a single publisher. This
    publisher will be subscribed as soon as this operator is subscribed the
    first time.

    On unsubscription of the last subscriber the depentent publisher will also
    be unsubscripted.
    """
    def __init__(self, publisher: Publisher) -> None:
        super().__init__()
        self._publisher = publisher

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        if len(self._subscriptions) == 1:  # if this was the first subscription
            self._publisher.subscribe(self)
        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._publisher.unsubscribe(self)


class MultiOperator(Publisher, Subscriber):
    """ Base class for operators depending on multiple publishers. Like
    Operator all publishers will be subscribed on first subscription to this
    operator. Accordingly all publishers get unsubscribed on unsubscription
    of the last subscriber.
    """
    def __init__(self, *publishers: Publisher) -> None:
        super().__init__()
        self._publishers = publishers

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        if len(self._subscriptions) == 1:  # if this was the first subscription
            for _publisher in self._publishers:
                # subscribe to all dependent publishers
                _publisher.subscribe(self)
        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions:
            for _publisher in self._publishers:
                _publisher.unsubscribe(self)


def build_operator(operator_cls):
    """ This function is taking a operator class and is returning a function
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
