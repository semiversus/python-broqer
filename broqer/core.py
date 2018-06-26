from abc import ABCMeta, abstractmethod
from typing import Any, Callable


class Disposable(metaclass=ABCMeta):
    """ Implementation of the disposable pattern. Call .dispose() to free
            resource.

        >>> class MyDisposable(Disposable):
        ...     def dispose(self):
        ...         print('DISPOSED')

        >>> d = MyDisposable()
        >>> d.dispose()
        DISPOSED
        >>> with MyDisposable():
        ...     print('working')
        working
        DISPOSED
    """
    @abstractmethod
    def dispose(self):
        """ .dispose() method has to be overwritten"""

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.dispose()


class SubscriptionDisposable(Disposable):
    def __init__(self, publisher: 'Publisher', subscriber: 'Subscriber') \
            -> None:
        self._publisher = publisher
        self._subscriber = subscriber

    def dispose(self) -> None:
        self._publisher.unsubscribe(self._subscriber)


class SubscriptionError(ValueError):
    pass


class Publisher():
    def __init__(self):
        self._subscriptions = set()

    def subscribe(self, subscriber: 'Subscriber') -> SubscriptionDisposable:
        if subscriber in self._subscriptions:
            raise SubscriptionError('Subscriber already registered')

        self._subscriptions.add(subscriber)
        return SubscriptionDisposable(self, subscriber)

    def unsubscribe(self, subscriber: 'Subscriber') -> None:
        try:
            self._subscriptions.remove(subscriber)
        except KeyError:
            raise SubscriptionError('Subscriber is not registered (anymore)')

    def notify(self, *args: Any) -> None:
        """ emit to all subscriptions """
        for subscriber in tuple(self._subscriptions):
            subscriber.emit(*args, who=self)

    def __contains__(self, subscriber: 'Subscriber'):
        return subscriber in self._subscriptions

    def __len__(self):
        """ number of subscriptions """
        return len(self._subscriptions)

    def __or__(self, build_subscriber: Callable[['Publisher'], 'Publisher']) \
            -> 'Publisher':
        # build_subscriber is called with `self` and returns a new publisher
        return build_subscriber(self)

    def __await__(self):
        from broqer.op import ToFuture  # lazy import due circular dependency
        return ToFuture(self).__await__()

    def to_future(self, timeout=None):
        from broqer.op import ToFuture  # lazy import due circular dependency
        return ToFuture(self, timeout)


class StatefulPublisher(Publisher):
    def __init__(self, *init):
        Publisher.__init__(self)
        if not init:
            self._state = None
        else:
            self._state = init

    def subscribe(self, subscriber: 'Subscriber') -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        if self._state is not None:
            subscriber.emit(*self._state, who=self)
        return disposable

    def notify(self, *args: Any) -> None:
        if self._state != args:
            self._state = args
            Publisher.notify(self, *args)

    def reset_state(self):
        self._state = None


class Subscriber(metaclass=ABCMeta):
    @abstractmethod
    def emit(self, *args: Any, who: Publisher) -> None:
        """ .emit(...) method has to be overwritten """
