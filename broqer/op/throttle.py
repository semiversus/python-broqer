import asyncio
from typing import Any, Tuple  # noqa: F401

from broqer import Publisher

from ._operator import Operator, build_operator


class Throttle(Operator):
    def __init__(self, publisher: Publisher, duration: float,
                 loop=None) -> None:
        assert duration >= 0, 'duration has to be positive'

        Operator.__init__(self, publisher)

        self._duration = duration
        self._loop = loop or asyncio.get_event_loop()
        self._call_later_handler = None  # type: asyncio.Handle
        self._cache = None  # type: Tuple[Any, ...]

    def emit(self, *args: Any, who: Publisher) -> None:
        assert who == self._publisher, 'emit from non assigned publisher'
        if self._call_later_handler is None:
            self._emit(*args)
            self._cache = None
            self._call_later_handler = self._loop.call_later(
                self._duration, self._wait_done_cb)
        else:
            self._cache = args

    def _wait_done_cb(self):
        if self._cache is not None:
            self._emit(*self._cache)
            self._cache = None
            self._call_later_handler = self._loop.call_later(
                self._duration, self._wait_done_cb)
        else:
            self._call_later_handler = None


throttle = build_operator(Throttle)
