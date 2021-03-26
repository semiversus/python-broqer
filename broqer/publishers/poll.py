""" Implementing PollPublisher """
import asyncio
from typing import Callable, Type, Callable, Any

from broqer.publisher import Publisher, TValue, SubscriptionDisposable
from broqer.subscriber import Subscriber


class PollPublisher(Publisher):
    """ A PollPublisher is periodically calling a given function and is using
    the returned value to notify the subscribers. When no subscriber is present,
    the polling function is not called.

    :param poll_cb: Function to be called
    :param interval: Time in seconds between polling calls
    """
    def __init__(self, poll_cb: Callable[[], Any], interval: float, *,
                 type_: Type[TValue] = None):
        Publisher.__init__(self, type_=type_)
        self.poll_cb = poll_cb
        self.interval = interval
        self._poll_handler = None

    def subscribe(self, subscriber: 'Subscriber',
                  prepend: bool = False) -> 'SubscriptionDisposable':
        if not self._subscriptions:
            # call poll_cb once to set internal state and schedule a _poll call
            self._state = self.poll_cb()
            loop = asyncio.get_event_loop()
            assert self._poll_handler is None, '_poll_handler already assigned'
            self._poll_handler = loop.call_later(self.interval, self._poll)

        return Publisher.subscribe(self, subscriber, prepend)

    def unsubscribe(self, subscriber: 'Subscriber') -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions:
            # when no subscription is left, cancel next _poll and reset state
            self._poll_handler.cancel()
            self._poll_handler = None
            self.reset_state()

    def _poll(self):
        assert self._poll_handler is not None

        value = self.poll_cb()
        Publisher.notify(self, value)

        loop = asyncio.get_event_loop()
        self._poll_handler = loop.call_later(self.interval, self._poll)

    def notify(self, value: TValue) -> None:
        """ PollPublisher does not support .notify calls """
        raise ValueError(self.notify.__doc__)
