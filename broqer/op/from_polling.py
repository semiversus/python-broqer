"""
Call ``func(*args, **kwargs)`` periodically and emit the returned values

Usage:

>>> import asyncio
>>> import itertools
>>> from broqer import op

>>> _d = op.FromPolling(0.015, itertools.count().__next__) | op.sink(print)
0
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.07))
1
2
...
>>> _d.dispose()

>>> def foo(arg):
...   print('Foo:', arg)

>>> _d = op.FromPolling(0.015, foo, 5) | op.sink()
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
    def __init__(self, interval, poll_func: Callable[[Any], Any], *args,
                 error_callback=default_error_handler, loop=None,
                 **kwargs) -> None:
        super().__init__()

        self._interval = interval
        if args or kwargs:
            self._poll_func = \
                partial(poll_func, *args, **kwargs)  # type: Callable
        else:
            self._poll_func = poll_func  # type: Callable
        self._loop = loop or asyncio.get_event_loop()

        self._call_later_handler = None
        self._error_callback = error_callback

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = Publisher.subscribe(self, subscriber)
        if self._call_later_handler is None:
            self._poll_callback()
        return disposable

    def _poll_callback(self):
        if self._subscriptions:
            try:
                result = self._poll_func()
                if result is None:
                    result = ()
                elif not isinstance(result, tuple):
                    result = (result, )
                self._emit(*result)
            except Exception:
                self._error_callback(*sys.exc_info())

            self._call_later_handler = asyncio.get_event_loop().call_later(
                self._interval, self._poll_callback)
        else:
            self._call_later_handler = None
