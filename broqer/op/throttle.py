"""
Rate limit emits by the given time.

Usage:

>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()
>>> throttle_publisher = s | op.throttle(0.1)
>>> _d = throttle_publisher | op.sink(print)
>>> s.emit(1)
1
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> s.emit(3)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.2))
3

It's also possible to reset the throttling duration:

>>> s.emit(4)
4
>>> s.emit(5)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> throttle_publisher.reset()
5
"""
import asyncio
import sys
from typing import Any  # noqa: F401

from broqer import Publisher, default_error_handler, UNINITIALIZED

from .operator import Operator, build_operator


class Throttle(Operator):
    def __init__(self, publisher: Publisher, duration: float,
                 error_callback=default_error_handler, loop=None) -> None:
        assert duration >= 0, 'duration has to be positive'

        Operator.__init__(self, publisher)

        self._duration = duration
        self._loop = loop or asyncio.get_event_loop()
        self._call_later_handler = None  # type: asyncio.Handle
        self._last_state = UNINITIALIZED  # type: Any
        self._error_callback = error_callback

    def get(self):
        Publisher.get(self)

    def emit(self, value: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._call_later_handler is None:
            self.notify(value)
            self._last_state = UNINITIALIZED
            self._call_later_handler = self._loop.call_later(
                self._duration, self._wait_done_cb)
        else:
            self._last_state = value

    def _wait_done_cb(self):
        if self._last_state is not UNINITIALIZED:
            try:
                self.notify(self._last_state)
            except Exception:  # pylint: disable=broad-except
                self._error_callback(*sys.exc_info())
            self._last_state = UNINITIALIZED
            self._call_later_handler = self._loop.call_later(
                self._duration, self._wait_done_cb)
        else:
            self._call_later_handler = None

    def reset(self):
        if self._call_later_handler is not None:
            self._call_later_handler.cancel()
            self._wait_done_cb()


throttle = build_operator(Throttle)  # pylint: disable=invalid-name
