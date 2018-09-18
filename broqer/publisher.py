""" Implementing Publisher and StatefulPublisher """

import asyncio
from typing import TYPE_CHECKING, Any, Union

from broqer import NONE, SubscriptionDisposable

if TYPE_CHECKING:
    from broqer import Subscriber  # noqa: F401 pylint: disable=unused-import


class SubscriptionError(ValueError):
    """ Special exception raised when subscription is failing (subscriber
    already subscribed) or on unsubscribe when subscriber is not subscribed
    """
    pass


class Publisher():
    """ In broqer a subscriber can subscribe to a Publisher. Subscribers
    are notified about emitted values from the publisher. In other frameworks
    publisher/subscriber are referenced as observable/observer.

    As information receiver use following method to interact with Publisher
    .subscribe(subscriber) to subscribe for events on this publisher
    .unsubscribe(subscriber) to unsubscribe
    .get() to get the current state (will raise ValueError if not stateful)

    When implementing a Publisher use the following methods:
    .notify(value) calls .emit(value) on all subscribers

    :ivar _subscriptions: holding a list of subscribers
    """
    def __init__(self):
        self._subscriptions = list()

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        """ Subscribing the given subscriber.

        :param subscriber: subscriber to add
        :param prepend: For internal use - usually the subscribers will be
            added at the end of a list. When prepend is True, it will be added
            in front of the list. This will habe an effect in the order the
            subscribers are called.
        :raises SubscriptionError: if subscriber already subscribed
        """

        # `subscriber in self._subscriptions` is not working because
        # tuple.__contains__ is using __eq__ which is overwritten and returns
        # a new publisher - not helpful here
        if any(subscriber is s for s in self._subscriptions):
            raise SubscriptionError('Subscriber already registered')

        if prepend:
            self._subscriptions.insert(0, subscriber)
        else:
            self._subscriptions.append(subscriber)

        return SubscriptionDisposable(self, subscriber)

    def unsubscribe(self, subscriber: 'Subscriber') -> None:
        """ Unsubscribe the given subscriber

        :param subscriber: subscriber to unsubscribe
        :raises SubscriptionError: if subscriber is not subscribed (anymore)
        """
        # here is a special implementation which is replacing the more
        # obvious one: self._subscriptions.remove(subscriber) - this will not
        # work because list.remove(x) is doing comparision for equality.
        # Applied to publishers this will return another publisher instead of
        # a boolean result
        for i, _s in enumerate(self._subscriptions):
            if _s is subscriber:
                self._subscriptions.pop(i)
                return
        raise SubscriptionError('Subscriber is not registered')

    def get(self):  # pylint: disable=no-self-use
        """ Return the value of the publisher. This is only working for
        stateful publishers. If publisher is stateless it will raise a
        ValueError.

        :raises ValueError: when the publisher is stateless.
        """
        raise ValueError('No value available')

    def notify(self, value: Any) -> asyncio.Future:
        """ Calling .emit(value) on all subscribers. A synchronouse subscriber
        will just return None, a asynchronous one may returns a future. Futures
        will be collected. If no future was returned None will be returned by
        this method. If one futrue was returned that future will be returned.
        When multiple futures were returned a gathered future will be returned.
        """
        results = (s.emit(value, who=self) for s in self._subscriptions)
        futures = tuple(r for r in results if r is not None)

        if not futures:
            return None

        if len(futures) == 1:
            return futures[0]  # return the received single future

        return asyncio.gather(*futures)

    @property
    def subscriptions(self):
        """ Property returning a tuple with all current subscribers """
        return tuple(self._subscriptions)

    def __or__(self, subscriber: 'Subscriber'
               ) -> Union[SubscriptionDisposable, 'Publisher', 'Subscriber']:
        return subscriber.__ror__(self)

    def __await__(self):
        """ Publishers are awaitable and the future is done when the publisher
        emits a value """
        from broqer.op import OnEmitFuture  # due circular dependency
        return (self | OnEmitFuture(timeout=None)).__await__()

    def wait_for(self, timeout=None):
        """ When a timeout should be applied for awaiting use this method """
        from broqer.op import OnEmitFuture  # due circular dependency
        return self | OnEmitFuture(timeout=timeout)

    def __bool__(self):
        """ A new Publisher is the result of a comparision between a publisher
        and something else (may also be a second publisher). This result should
        never be used in a boolean sense (e.g. in `if p1 == p2:`). To prevent
        this __bool__ is overwritten to raise a ValueError.
        """
        raise ValueError('Evaluation of comparison of publishers is not '
                         'supported')


class StatefulPublisher(Publisher):
    """ A StatefulPublisher is keeping it's state. This changes the behavior
    compared to a non-stateful Publisher:
    - when subscribing the subscriber will be notified with the actual state
    - .get() is returning the actual state

    :param init: the initial state. As long the state is NONE, the
        behavior will be equal to a stateless Publisher.
    """
    def __init__(self, init=NONE):
        Publisher.__init__(self)
        self._state = init

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend=prepend)

        # if a state is defined emit it during .subscribe call
        if self._state is not NONE:
            subscriber.emit(self._state, who=self)

        return disposable

    def get(self):
        """ Returns state if defined else it raises a ValueError """
        if self._state is not NONE:
            return self._state
        return Publisher.get(self)  # raises ValueError

    def notify(self, value: Any) -> asyncio.Future:
        """ Only notifies subscribers if state has changed """
        if self._state == value:
            return None

        self._state = value
        return Publisher.notify(self, value)

    def reset_state(self, value=NONE):
        """ Resets the state. Behavior for .subscribe() and .get() will be
        like a stateless Publisher until next .emit()
        """
        self._state = value
