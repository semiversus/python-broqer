"""
Apply ``func(*args, value, **kwargs)`` to each emitted value. It's also
possible to omit ``func`` - in this case it's acting as dummy subscriber

Usage:

>>> from broqer import Value, op, Sink
>>> s = Value()

>>> len(s.subscriptions)
0
>>> _d = s.subscribe(Sink(print, 'Sink', sep=':'))
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
from typing import Any, Callable, Optional, TYPE_CHECKING

from broqer import Subscriber

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from broqer import Publisher


class Sink(Subscriber):  # pylint: disable=too-few-public-methods
    """ Apply ``function(*args, value, **kwargs)`` to each emitted value. It's
    also possible to omit ``function`` - in this case it's acting as dummy
    subscriber

    :param function: function to be called when source publisher emits
    :param \\*args: variable arguments to be used for calling function
    :param unpack: value from emits will be unpacked (\\*value)
    :param \\*\\*kwargs: keyword arguments to be used for calling function
    """
    def __init__(self,  # pylint: disable=keyword-arg-before-vararg
                 function: Optional[Callable[..., None]] = None,
                 *args, unpack=False, **kwargs) -> None:
        if function is None:
            self._function = None  # type: Optional[Callable[..., None]]
        elif args or kwargs:
            self._function = \
                partial(function, *args, **kwargs)
        else:
            self._function = function

        self._unpack = unpack

    def emit(self, value: Any, who: 'Publisher'):
        if self._function:
            if self._unpack:
                self._function(*value)
            else:
                self._function(value)


def build_sink(function: Callable[..., None] = None, *,
               unpack: bool = False):
    """ Decorator to wrap a function to return a Sink subscriber.

    :param function: function to be wrapped
    :param unpack: value from emits will be unpacked (*value)
    """
    def _build_sink(function):
        return Sink(function, unpack=unpack)

    if function:
        return _build_sink(function)

    return _build_sink


def build_sink_factory(function: Callable[..., None] = None, *,
                       unpack: bool = False):
    """ Decorator to wrap a function to return a Sink subscriber factory.
    :param function: function to be wrapped
    :param unpack: value from emits will be unpacked (*value)
    """
    def _build_sink(function: Callable[..., None]):
        @wraps(function)
        def _wrapper(*args, **kwargs) -> Sink:
            if 'unpack' in kwargs:
                raise TypeError('"unpack" has to be defined by decorator')
            return Sink(function, *args, unpack=unpack, **kwargs)
        return _wrapper

    if function:
        return _build_sink(function)

    return _build_sink


def sink_property(function: Callable[..., None] = None, unpack: bool = False):
    """ Decorator to build a property returning a Sink subscriber.
    :param function: function to be wrapped
    :param unpack: value from emits will be unpacked (*value)
    """
    def build_sink_property(function):
        @property
        def _build_sink(self):
            return Sink(function, self, unpack=unpack)
        return _build_sink

    if function:
        return build_sink_property(function)

    return build_sink_property
