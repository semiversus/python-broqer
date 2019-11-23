"""
Rate limit emits by the given time.

Usage:

>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()
>>> throttle_publisher = s | op.Throttle(0.1)
>>> _d = throttle_publisher | op.Sink(print)
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

from broqer.publisher import Publisher
from broqer.types import NONE
from broqer.default_error_handler import default_error_handler

from .operator import Operator


class Throttle(Operator):
    """ Rate limit emits by the given time.

    :param duration: time for throttling in seconds
    :param error_callback: the error callback to be registered
    :param loop: asyncio event loop to use
    """
    def __init__(self, duration: float,
                 error_callback=default_error_handler, loop=None) -> None:
        if duration < 0:
            raise ValueError('Duration has to be bigger than zero')

        Operator.__init__(self)

        self._duration = duration
        self._loop = loop or asyncio.get_event_loop()
        self._call_later_handler = None  # type: asyncio.Handle
        self._last_state = NONE  # type: Any
        self._error_callback = error_callback

    def get(self):
        Publisher.get(self)

    def emit_op(self, value: Any, who: Publisher) -> None:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        if self._call_later_handler is None:
            self._last_state = value
            self._wait_done_cb()
        else:
            self._last_state = value

    def _wait_done_cb(self):
        if self._last_state is not NONE:
            try:
                self.notify(self._last_state)
            except Exception:  # pylint: disable=broad-except
                self._error_callback(*sys.exc_info())
            self._last_state = NONE
            self._call_later_handler = self._loop.call_later(
                self._duration, self._wait_done_cb)
        else:
            self._call_later_handler = None

    def reset(self):
        """ Reseting duration for throttling """
        if self._call_later_handler is not None:
            self._call_later_handler.cancel()
            self._call_later_handler = None
            self._wait_done_cb()
