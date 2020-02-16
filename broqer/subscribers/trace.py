""" Implements Trace subscriber """
from time import time
from typing import TYPE_CHECKING, Any, Callable, Optional

from .sink import Sink

if TYPE_CHECKING:
    # pylint: disable=cyclic-import
    from broqer import Publisher


class Trace(Sink):
    """ Trace is a subscriber used for debugging purpose. On subscription
    it will use the prepend flag to be the first callback called when the
    publisher of interest is emitting.
    :param callback: optional function to call
    :param \\*args: arguments used additionally when calling callback
    :param unpack: value from emits will be unpacked (\\*value)
    :param label: string to be used on output
    :param \\*\\*kwargs: keyword arguments used when calling callback
    """
    def __init__(self,  # pylint: disable=keyword-arg-before-vararg
                 function: Optional[Callable[..., None]] = None,
                 *args, unpack=False, label=None, **kwargs) -> None:
        Sink.__init__(self, function, *args, unpack=unpack, **kwargs)
        self._label = label

    def emit(self, value: Any, who: 'Publisher'):
        self._trace_handler(who, value, label=self._label)
        Sink.emit(self, value, who=who)

    @classmethod
    def set_handler(cls, handler):
        """ Setting the handler for tracing information """
        cls._trace_handler = handler

    _timestamp_start = time()

    @staticmethod
    def _trace_handler(publisher: 'Publisher', value, label=None):
        """ Default trace handler is printing the timestamp, the publisher name
        and the emitted value
        """
        line = '--- %8.3f: ' % (time() - Trace._timestamp_start)
        line += repr(publisher) if label is None else label
        line += ' %r' % (value,)
        print(line)
