"""
Emit every value delayed by the given time.

Usage:

>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()
>>> s | op.Delay(0.1) | op.Sink(print)
<...>
>>> s.emit(1)
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> s.emit(3)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.07))
1
2
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
3

"""
import asyncio
import sys
from typing import Any

from broqer import Publisher, default_error_handler

from .operator import Operator


class Delay(Operator):
    """ Emit every value delayed by the given time.

    :param duration: time of delay in seconds
    :param error_callback: the error callback to be registered
    :param loop: asyncio event loop to use
    """
    def __init__(self, duration: float,
                 error_callback=default_error_handler, loop=None) -> None:

        if duration < 0:
            raise ValueError('delay has to be positive')

        Operator.__init__(self)

        self._duration = duration
        self._loop = loop or asyncio.get_event_loop()
        self._error_callback = error_callback

    def get(self):
        return Publisher.get(self)  # will raise ValueError

    def emit(self, value: Any, who: Publisher) -> None:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        self._loop.call_later(self._duration, self._delayed, value)

    def _delayed(self, value):
        try:
            self.notify(value)
        except Exception:  # pylint: disable=broad-except
            self._error_callback(*sys.exc_info())
