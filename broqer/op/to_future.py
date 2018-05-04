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

>>> _ = asyncio.get_event_loop().call_later(0.05, s.emit, 1, 2)
>>> asyncio.get_event_loop().run_until_complete(s)
(1, 2)
"""
import asyncio
from typing import Any

from broqer import Publisher, Subscriber

from ._operator import build_operator


class ToFuture(Subscriber):
    def __init__(self, publisher, timeout=None, loop=None):
        self._disposable = publisher.subscribe(self)

        if loop is None:
            loop = asyncio.get_event_loop()
        try:
            self._future = loop.create_future()
        except AttributeError:  # handling python <3.5.2
            self._future = asyncio.Future(loop=loop)
        self._future.add_done_callback(self._future_done)

        if timeout is not None:
            self._timeout_handle = loop.call_later(timeout, self._timeout)
        else:
            self._timeout_handle = None

    def _timeout(self):
        self._future.set_exception(asyncio.TimeoutError)

    def _future_done(self, future):
        self._disposable.dispose()
        if self._timeout_handle is not None:
            self._timeout_handle.cancel()

    def __await__(self):
        return self._future.__await__()

    def emit(self, *args: Any, who: Publisher) -> None:
        # handle special case: _disposable is set after
        # publisher.subscribe(self) in __init__
        assert not hasattr(self, '_disposable') or \
            who == self._disposable._publisher, \
            'emit comming from non assigned publisher'
        if len(args) == 1:
            self._future.set_result(args[0])
        else:
            self._future.set_result(args)


to_future = build_operator(ToFuture)
