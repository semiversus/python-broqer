"""
Emit the last received value periodically

Usage:

>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()

>>> sample_publisher = s | op.sample(0.015)
>>> sample_publisher.state == None
True
>>> _d = sample_publisher | op.sink(print, 'Sample:')

>>> s.emit(1)
Sample: 1
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.06))
Sample: 1
...
Sample: 1
>>> sample_publisher.state
(1,)

>>> s.emit(2, 3)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.06))
Sample: 2 3
...
Sample: 2 3
>>> sample_publisher.state
(2, 3)

>>> _d2 = sample_publisher | op.sink(print, 'Sample 2:')
Sample 2: 2 3
>>> _d.dispose()
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.06))
Sample 2: 2 3
...
Sample 2: 2 3

>>> len(s) # how many subscriber are registred
1
>>> _d2.dispose()
>>> len(s)
0
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.02))
"""
import asyncio
import sys
from typing import Any, Optional, Tuple  # noqa: F401

from broqer import Publisher, Subscriber, SubscriptionDisposable, \
                   default_error_handler

from ._operator import Operator, build_operator


class Sample(Operator):
    def __init__(self, publisher: Publisher, interval: float,
                 error_callback=default_error_handler, loop=None) -> None:
        assert interval > 0, 'interval has to be positive'

        Operator.__init__(self, publisher)

        self._interval = interval
        self._call_later_handle = None
        self._loop = loop or asyncio.get_event_loop()
        self._state = None  # type: Tuple
        self._error_callback = error_callback

    def subscribe(self, subscriber: Subscriber) -> SubscriptionDisposable:
        disposable = super().subscribe(subscriber)
        if self._state is not None:
            subscriber.emit(*self._state, who=self)
        return disposable

    def _periodic_callback(self):
        """ will be started on first emit """
        try:
            self.notify(*self._state)  # emit to all subscribers
        except Exception:
            self._error_callback(*sys.exc_info())

        if self._subscriptions:
            # if there are still subscriptions register next _periodic callback
            self._call_later_handle = \
                self._loop.call_later(self._interval, self._periodic_callback)
        else:
            self._state = None
            self._call_later_handle = None

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        self._state = args

        if self._call_later_handle is None:
            self._periodic_callback()

    @property
    def state(self):
        return self._state


sample = build_operator(Sample)
