import asyncio
from typing import Any, Callable, TYPE_CHECKING
import operator

from broqer.core import UNINITIALIZED, SubscriptionDisposable

if TYPE_CHECKING:
    from broqer.core import Subscriber  # noqa: F401


class SubscriptionError(ValueError):
    pass


class Publisher():
    def __init__(self):
        self._subscriptions = set()

    def subscribe(self, subscriber: 'Subscriber') -> 'SubscriptionDisposable':
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
               '__add__', '__and__', '__lshift__', '__mod__', '__mul__',
               '__pow__', '__rshift__', '__sub__', '__xor__', '__concat__',
               '__contains__', '__getitem__'):
    def _op(a, b, method=method):
        from broqer.op import CombineLatest, Map

        if isinstance(b, Publisher):
            return CombineLatest(a, b, map_=getattr(operator, method))
        else:
            return Map(a, getattr(operator, method), b)

    setattr(Publisher, method, _op)

for method, _method in (('__radd__', '__add__'), ('__rand__', '__and__'),
                        ('__rlshift__', '__lhift__'), ('__rmod__', '__mod__'),
                        ('__rmul__', '__mul__'), ('__rpow__', '__pow__'),
                        ('__rrshift__', '__rshift__'), ('__rsub__', '__sub__'),
                        ('__rxor__', '__xor__')):
    def _op(a, b, method=_method):
        from broqer.op import Map

        return Map(a, getattr(operator, method), b)

    setattr(Publisher, method, _op)


class StatefulPublisher(Publisher):
    def __init__(self, init=UNINITIALIZED):
        Publisher.__init__(self)
        self._state = init

    def subscribe(self, subscriber: 'Subscriber') -> 'SubscriptionDisposable':
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
