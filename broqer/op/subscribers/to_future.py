"""
Build a future able to await for

Usage:

>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()

>>> _ = asyncio.get_event_loop().call_later(0.05, s.emit, 1)

>>> asyncio.get_event_loop().run_until_complete(s | op.to_future() )
1
>>> asyncio.get_event_loop().run_until_complete(s | op.to_future(0.05) )
Traceback (most recent call last):
...
concurrent.futures._base.TimeoutError

>>> _ = asyncio.get_event_loop().call_later(0.05, s.emit, (1, 2))
>>> asyncio.get_event_loop().run_until_complete(s)
(1, 2)
"""
import asyncio
from typing import Any, Optional

from broqer import Publisher, Subscriber

from broqer.op.operator import build_operator


class ToFuture(Subscriber, asyncio.Future):
    """ Build a future able to await for.
    :param publisher: source publisher
    :param timeout: timeout in seconds
    :param loop: asyncio loop to be used
    """
    def __init__(self, publisher, timeout=None, loop=None):
        asyncio.Future.__init__(self, loop=loop)
        if loop is None:
            loop = asyncio.get_event_loop()

        self.add_done_callback(self._future_done)

        if timeout is not None:
            self._timeout_handle = loop.call_later(timeout, self._timeout)
        else:
            self._timeout_handle = None

        self._disposable = None
        self._disposable = publisher.subscribe(self)
        if self.done():
            self._disposable.dispose()
            self._disposable = None

    def _timeout(self):
        self.set_exception(asyncio.TimeoutError)

    def _future_done(self, _future):
        if self._disposable is not None:
            self._disposable.dispose()
            self._disposable = None
        if self._timeout_handle is not None:
            self._timeout_handle.cancel()

    def emit(self, value: Any,
             who: Optional[Publisher] = None  # pylint: disable=unused-argument
             ) -> None:
        if self._disposable is not None:
            self._disposable.dispose()
            self._disposable = None
        if not self.cancelled():
            self.set_result(value)


to_future = build_operator(ToFuture)  # pylint: disable=invalid-name
