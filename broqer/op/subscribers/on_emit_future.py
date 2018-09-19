"""
Build a future able to await for

Usage:

>>> import asyncio
>>> from broqer import Subject, op
>>> s = Subject()

>>> _ = asyncio.get_event_loop().call_later(0.05, s.emit, 1)

>>> asyncio.get_event_loop().run_until_complete(s | op.OnEmitFuture() )
1

#>>> _ = asyncio.get_event_loop().call_later(0.05, s.emit, (1, 2))
#>>> asyncio.get_event_loop().run_until_complete(s)
(1, 2)
"""
import asyncio
from typing import Any, Optional

from broqer import Publisher, Subscriber


class OnEmitFuture(Subscriber, asyncio.Future):
    """ Build a future able to await for.
    :param publisher: source publisher
    :param timeout: timeout in seconds
    :param loop: asyncio loop to be used
    """
    def __init__(self, timeout=None, loop=None):
        asyncio.Future.__init__(self, loop=loop)

        if loop is None:
            loop = asyncio.get_event_loop()

        self.add_done_callback(self._cleanup)

        if timeout is not None:
            self._timeout_handle = loop.call_later(
                timeout, self.set_exception, asyncio.TimeoutError)
        else:
            self._timeout_handle = None

        self._publisher = None

    def _cleanup(self, _future):
        self._publisher.unsubscribe(self)

        if self._timeout_handle is not None:
            self._timeout_handle.cancel()

    def emit(self, value: Any, who: Optional[Publisher] = None) -> None:
        assert who is self._publisher
        if not self.done():
            self.set_result(value)

    def __ror__(self, publisher: Publisher) -> Subscriber:
        self._publisher = publisher
        publisher.subscribe(self)
        return self
