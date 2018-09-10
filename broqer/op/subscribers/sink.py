"""
Apply ``func(*args, value, **kwargs)`` to each emitted value. It's also
possible to omit ``func`` - in this case the publisher will be subscribed, but
no function will be applied.

Usage:

>>> from broqer import Subject, op
>>> s = Subject()

>>> len(s.subscriptions)
0
>>> _d = s | op.sink(print, 'Sink', sep=':')
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
from functools import partial
from typing import Any, Callable, Optional

from broqer import Disposable, Publisher, Subscriber

from broqer.op.operator import build_operator


class Sink(Subscriber, Disposable):
    """ Apply ``callback(*args, value, **kwargs)`` to each emitted value. It's
    also possible to omit ``callback`` - in this case the publisher will be
    subscribed, but no function will be applied.

    :param publisher: source publisher
    :param callback: function to be called when source publisher emits
    :param \\*args: variable arguments to be used for calling callback
    :param unpack: value from emits will be unpacked as (*value)
    :param \\*kwargs: keyword arguments to be used for calling callback
    """
    def __init__(self,  # pylint: disable=keyword-arg-before-vararg
                 publisher: Publisher,
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
        self._disposable = publisher.subscribe(self)

    def emit(self, value: Any, who: Publisher):
        # handle special case: _disposable is set after
        # publisher.subscribe(self) in __init__
        assert not hasattr(self, '_disposable') or \
            who is self._disposable.publisher, \
            'emit comming from non assigned publisher'
        if self._callback:
            if self._unpack:
                self._callback(*value)
            else:
                self._callback(value)

    def dispose(self):
        self._disposable.dispose()


sink = build_operator(Sink)  # pylint: disable=invalid-name
