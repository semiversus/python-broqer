"""
Emit a value only after a given idle time (emits meanwhile are skipped).
Debounce can also be used for a timeout functionality.

Usage:

>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()
>>> _d = s | op.debounce(0.1) | op.sink(print)
>>> s.emit(1)
>>> s.emit(2)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> s.emit(3)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.15))
3
>>> _d.dispose()

When debounce is retriggered you can specify a value to emit:

>>> debounce_publisher = s | op.debounce(0.1, False)
>>> _d = debounce_publisher | op.sink(print)
>>> s.emit(False)
False
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.15))
>>> s.emit(True)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> s.emit(False)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.05))
>>> s.emit(True)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.15))
True

Reseting is also possible:

>>> s.emit(False)
False
>>> s.emit(True)
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.15))
True
>>> debounce_publisher.reset()
False
>>> asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.15))

>>> _d.dispose()
"""
import asyncio
import sys
from typing import Any  # noqa

from broqer import Publisher, Subscriber, default_error_handler, UNINITIALIZED

from ._operator import Operator, build_operator


class Debounce(Operator):
    def __init__(self, publisher: Publisher, duetime: float,
                 retrigger_value: Any = UNINITIALIZED,
                 error_callback=default_error_handler,
                 loop=None) -> None:
        assert duetime >= 0, 'duetime has to be positive'

        Operator.__init__(self, publisher)

        self.duetime = duetime
        self._retrigger_value = retrigger_value
        self._loop = loop or asyncio.get_event_loop()
        self._call_later_handler = None  # type: asyncio.Handle
        self._error_callback = error_callback
        self._state = UNINITIALIZED  # type: Any
        self._next_state = UNINITIALIZED  # type: Any

    def unsubscribe(self, subscriber: Subscriber) -> None:
        Operator.unsubscribe(self, subscriber)
        if not self._subscriptions:
            self._state = UNINITIALIZED
            if self._call_later_handler:
                self._call_later_handler.cancel()

    def get(self):
        if self._retrigger_value is not UNINITIALIZED and (
                not self._subscriptions or self._state is UNINITIALIZED):
            return self._retrigger_value
        return self._state

    def emit(self, value: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'

        if value == self._next_state:
            # skip if emit will result in the same value as the scheduled one
            return

        if self._call_later_handler:
            self._call_later_handler.cancel()

        if self._retrigger_value is not UNINITIALIZED and \
           self._state != self._retrigger_value:
            # when retrigger_value is defined and current state is different
            self.notify(self._retrigger_value)
            self._state = self._retrigger_value
            self._next_state = self._retrigger_value
            if value == self._retrigger_value:
                # skip if emit will result in the same value as the current one
                return

        if value == self._state:
            self._next_state = self._state
            return

        self._next_state = value

        self._call_later_handler = \
            self._loop.call_later(self.duetime, self._debounced)

    def _debounced(self):
        self._call_later_handler = None
        try:
            self.notify(self._next_state)
            self._state = self._next_state
        except Exception:  # pylint: disable=broad-except
            self._error_callback(*sys.exc_info())

    def reset(self):
        if self._retrigger_value is not UNINITIALIZED:
            self.notify(self._retrigger_value)
            self._state = self._retrigger_value
            self._next_state = self._retrigger_value
        if self._call_later_handler:
            self._call_later_handler.cancel()


debounce = build_operator(Debounce)  # pylint: disable=invalid-name
