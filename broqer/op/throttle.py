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
from typing import Any  # noqa: F401

from broqer import Publisher, default_error_handler, NONE

from broqer.operator import Operator, OperatorFactory
from broqer.timer import Timer


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
        self._timer = Timer(self._delayed_emit_cb, loop=loop)
        self._error_callback = error_callback

    def get(self):
        return Publisher.get(self)

    def emit(self, value: Any, who: Publisher) -> None:
        if who is not self._orginator:
            raise ValueError('Emit from non assigned publisher')

        if not self._timer.is_running():
            self._timer.start(timeout=0, args=(value,))
        else:
            self._timer.change_arguments(args=(value,))

    def _delayed_emit_cb(self, value=NONE):
        if value is NONE:
            # since the last emit the given duration has passed without another
            # emit
            return

        try:
            Publisher.notify(self, value)
        except Exception:  # pylint: disable=broad-except
            self._error_callback(*sys.exc_info())

        self._timer.start(self._duration)

    def reset(self):
        """ Reseting duration for throttling """
        self._timer.cancel()


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
