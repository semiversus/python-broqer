"""
Call ``func(*args, **kwargs)`` periodically and emit the returned values

Usage:

>>> import asyncio
>>> import itertools
>>> from broqer import op

>>> _d = op.FromPolling(0.015, itertools.count().__next__) | op.Sink(print)
0
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.07))
1
2
...
>>> _d.dispose()

>>> def foo(arg):
...   print('Foo:', arg)

>>> _d = op.FromPolling(0.015, foo, 5) | op.Sink()
Foo: 5
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
Foo: 5
...
Foo: 5
>>> _d.dispose()
"""
import asyncio
from functools import partial
import sys
from typing import Any, Callable

from broqer import Publisher, Subscriber, SubscriptionDisposable, \
                   default_error_handler


class FromPolling(Publisher):
    """ Call ``func(*args, **kwargs)`` periodically and emit the returned
    values.
    :param interval: periodic interval in seconds. Use None if it should poll
        only once on first subscription
    :param poll_func: function to be called
    :param \\*args: variable arguments to be used for calling poll_func
    :param error_callback: error callback to be registered
    :param loop: asyncio event loop to use
    :param \\*kwargs: keyword arguments to be used for calling poll_func
    """
    def __init__(self, interval, poll_func: Callable[[Any], Any], *args,
                 error_callback=default_error_handler, loop=None,
                 **kwargs) -> None:
        Publisher.__init__(self)

        self._interval = interval
        if args or kwargs:
            self._poll_func = \
                partial(poll_func, *args, **kwargs)  # type: Callable
        else:
            self._poll_func = poll_func  # type: Callable
        self._loop = loop or asyncio.get_event_loop()

        self._call_later_handler = None
        self._error_callback = error_callback

    def subscribe(self, subscriber: Subscriber,
                  prepend: bool = False) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber, prepend)
        if self._interval is None:
            try:
                result = self._poll_func()
                subscriber.emit(result, who=self)
            except Exception:  # pylint: disable=broad-except
                self._error_callback(*sys.exc_info())
        elif self._call_later_handler is None:
            self._poll_callback()
        return disposable

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Publisher.unsubscribe(self, subscriber)
        if not self._subscriptions and self._call_later_handler:
            self._call_later_handler.cancel()
            self._call_later_handler = None

    def get(self):
        Publisher.get(self)  # raises ValueError

    def _poll_callback(self):
        try:
            result = self._poll_func()
            self.notify(result)
        except Exception:  # pylint: disable=broad-except
            self._error_callback(*sys.exc_info())

        self._call_later_handler = self._loop.call_later(
            self._interval, self._poll_callback)
