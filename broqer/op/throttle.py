"""
Rate limit emits by the given time.
Usage:
>>> import asyncio
>>> from broqer import Value, op, Sink
>>> v = Value()
>>> throttle_publisher = v | op.Throttle(0.1)
>>> _d = throttle_publisher.subscribe(Sink(print))
>>> v.emit(1)
1
>>> v.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> v.emit(3)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.2))
3
>>> # It's also possible to reset the throttling duration:
>>> v.emit(4)
4
>>> v.emit(5)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> throttle_publisher.reset()
"""
import asyncio
import sys
from typing import Any, Optional  # noqa: F401

from broqer import Publisher, default_error_handler, NONE

from broqer.operator import Operator, OperatorFactory


class AppliedThrottle(Operator):
    """ Rate limit emits by the given time.
    :param duration: time for throttling in seconds
    :param error_callback: the error callback to be registered
    :param loop: asyncio event loop to use
    """
    def __init__(self, publisher: Publisher, duration: float,
                 error_callback=default_error_handler, loop=None) -> None:

        Operator.__init__(self, publisher)

        self._duration = duration
        self._loop = loop or asyncio.get_event_loop()
        self._call_later_handler = None  # type: Optional[asyncio.Handle]
        self._last_state = NONE  # type: Any
        self._error_callback = error_callback

    def get(self):
        return Publisher.get(self)

    def emit(self, value: Any, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        if self._call_later_handler is None:
            self._last_state = value
            self._wait_done_cb()
        else:
            self._last_state = value

    def _wait_done_cb(self):
        if self._last_state is not NONE:
            try:
                Publisher.notify(self, self._last_state)
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


class Throttle(OperatorFactory):  # pylint: disable=too-few-public-methods
    """ Apply throttling to each emitted value.
    :param duration: time for throttling in seconds
    """
    def __init__(self, duration: float) -> None:
        if duration < 0:
            raise ValueError('Duration has to be bigger than zero')

        self._duration = duration

    def apply(self, publisher: Publisher):
        return AppliedThrottle(publisher, self._duration)
