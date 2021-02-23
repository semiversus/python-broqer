"""
Build a future able to await for

Usage:

>>> import asyncio
>>> from broqer import Value, op, OnEmitFuture
>>> s = Value()

>>> _ = asyncio.get_event_loop().call_later(0.05, s.emit, 1)

>>> asyncio.get_event_loop().run_until_complete(OnEmitFuture(s) )
1

#>>> _ = asyncio.get_event_loop().call_later(0.05, s.emit, (1, 2))
#>>> asyncio.get_event_loop().run_until_complete(s)
(1, 2)
"""
import asyncio
from typing import Any, Optional, TYPE_CHECKING

import broqer

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from broqer import Publisher


class OnEmitFuture(broqer.Subscriber, asyncio.Future):
    """ Build a future able to await for.
    :param publisher: source publisher
    :param timeout: timeout in seconds, None for no timeout
    :param omit_subscription: omit any emit while subscription
    :param loop: asyncio loop to be used
    """
    def __init__(self, publisher: 'Publisher', timeout=None,
                 omit_subscription=False, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()

        asyncio.Future.__init__(self, loop=loop)
        self.add_done_callback(self._cleanup)

        self._publisher = publisher

        self._omit_subscription = omit_subscription

        if timeout is not None:
            self._timeout_handle = loop.call_later(
                timeout, self.set_exception, asyncio.TimeoutError)
        else:
            self._timeout_handle = None

        publisher.subscribe(self)
        self._omit_subscription = False

    def _cleanup(self, _future=None):
        self._publisher.unsubscribe(self)

        if self._timeout_handle is not None:
            self._timeout_handle.cancel()
            self._timeout_handle = None

    def emit(self, value: Any, who: Optional['Publisher'] = None) -> None:
        if who is not self._publisher:
            raise ValueError('Emit from non assigned publisher')

        if self._omit_subscription:
            return

        if not self.done():
            self.remove_done_callback(self._cleanup)
            self._cleanup()
            self.set_result(value)
