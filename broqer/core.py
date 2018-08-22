import asyncio
from abc import ABCMeta, abstractmethod
from typing import Any, Callable


class UNINITIALIZED:
    """ marker class used for initialization of state """
    pass


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

    def __exit__(self, _type, _value, _traceback):
        self.dispose()


class SubscriptionDisposable(Disposable):
    def __init__(self, publisher: 'Publisher', subscriber: 'Subscriber') \
            -> None:
        self._publisher = publisher
        self._subscriber = subscriber

    def dispose(self) -> None:
        self._publisher.unsubscribe(self._subscriber)

    @property
    def publisher(self):
        return self._publisher

    @property
    def subscriber(self):
        return self._subscriber


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

    def get(self):  # pylint: disable=useless-return, no-self-use
        """Return the value of a (possibly simulated) subscription to this
        publisher
        """
        raise ValueError('No value available')

    def notify(self, value: Any) -> asyncio.Future:
        """ emit to all subscriptions """
        results = (s.emit(value, who=self) for s in tuple(self._subscriptions))
        futures = tuple(r for r in results if r is not None)

        if futures:
            if len(futures) == 1:
                return futures[0]
            return asyncio.gather(*futures)
        return None

    def __contains__(self, subscriber: 'Subscriber'):
        return subscriber in self._subscriptions

    def __len__(self):
        """ number of subscriptions """
        return len(self._subscriptions)

    @property
    def subscriptions(self):
        return tuple(self._subscriptions)

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

    for method in ('__lt__', '__le__', '__eq__', '__ne__', '__ge__', '__gt__',
        '__add__', '__and__', '__lshift__', '__mod__', '__mul__', '__pow__',
        '__rshift__', '__sub__', '__xor__', '__concat__', '__contains__',
        '__getitem__'):
        def _op(a ,b, method=method):
            from .op import CombineLatest
            return CombineLatest(a, b, map=getattr(operator, method))
        setattr(Publisher, method, _op)


class StatefulPublisher(Publisher):
    def __init__(self, init=UNINITIALIZED):
        Publisher.__init__(self)
        self._state = init

    def subscribe(self, subscriber: 'Subscriber') -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        if self._state is not UNINITIALIZED:
            subscriber.emit(self._state, who=self)
        return disposable

    def get(self):
        if self._state is not UNINITIALIZED:
            return self._state
        return Publisher.get(self)

    def notify(self, value: Any) -> asyncio.Future:
        if self._state != value:
            self._state = value
            return Publisher.notify(self, value)
        return None

    def reset_state(self, value=UNINITIALIZED):
        self._state = value


class Subscriber(metaclass=ABCMeta):  # pylint: disable=too-few-public-methods
    @abstractmethod
    def emit(self, value: Any, who: Publisher) -> asyncio.Future:
        """Send new value to the subscriber
        :param value: value to be send
        :param who: reference to which publisher is emitting
        """

    def __call__(self, publisher: Publisher):
        return publisher.subscribe(self)
