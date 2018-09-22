"""
Apply ``func(*args, value, **kwargs)`` to each emitted value. It's also
possible to omit ``func`` - in this case it's acting as dummy subscriber

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> len(s.subscriptions)
0
>>> _d = s | op.Sink(print, 'Sink', sep=':')
>>> len(s.subscriptions)
1

>>> s.emit(1)
Sink:1
>>> s.emit((1, 2))
Sink:(1, 2)

>>> _d.dispose()
>>> len(s.subscriptions)
0
"""
from functools import partial, wraps
from typing import Any, Callable, Optional

from broqer import Subscriber, Publisher


class Sink(Subscriber):  # pylint: disable=too-few-public-methods
    """ Apply ``callback(*args, value, **kwargs)`` to each emitted value. It's
    also possible to omit ``callback`` - in this case it's acting as dummy
    subscriber

    :param callback: function to be called when source publisher emits
    :param \\*args: variable arguments to be used for calling callback
    :param unpack: value from emits will be unpacked as (*value)
    :param \\**kwargs: keyword arguments to be used for calling callback
    """
    def __init__(self,  # pylint: disable=keyword-arg-before-vararg
                 callback: Optional[Callable[..., None]] = None,
                 *args, unpack=False, **kwargs) -> None:
        if callback is None:
            self._callback = None  # type: Callable
        elif args or kwargs:
            self._callback = \
                partial(callback, *args, **kwargs)  # type: Callable
        else:
            self._callback = callback  # type: Callable

        self._unpack = unpack

    def emit(self, value: Any, who: Publisher):
        if self._callback:
            if self._unpack:
                self._callback(*value)
            else:
                self._callback(value)


def build_sink(function: Callable[..., None] = None,
               unpack: bool = False):
    def _build_sink(function: Callable[..., None]):
        @wraps(function)
        def _wrapper(*args, **kwargs) -> Sink:
            return Sink(function, *args, unpack=unpack, **kwargs)
        return _wrapper

    if function:
        return _build_sink(function)

    return _build_sink
