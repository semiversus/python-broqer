""" Broqer is a carefully crafted library to operate with continuous streams
of data in a reactive style with publish/subscribe and broker functionality.
"""

from .error_handler import default_error_handler
from .disposable import Disposable
from .types import NONE
from .publisher import Publisher, SubscriptionDisposable, SubscriptionError
from .subscriber import Subscriber
from .subscribers import (OnEmitFuture, Sink, Trace, build_sink,
                          build_sink_factory, sink_property, SinkAsync,
                          build_sink_async, build_sink_async_factory,
                          sink_async_property)
from .value import Value

from .operator_overloading import apply_operator_overloading

apply_operator_overloading()


__author__ = 'Günther Jena'
__email__ = 'guenther@jena.at'

try:
    from ._version import version as __version__
except ImportError:
    __version__ = 'not available'

__all__ = [
    'default_error_handler', 'Disposable', 'NONE', 'Publisher',
    'SubscriptionDisposable', 'SubscriptionError', 'Subscriber',
    'OnEmitFuture', 'Sink', 'Trace', 'build_sink', 'build_sink_factory',
    'sink_property', 'Value', 'op', 'SinkAsync', 'build_sink_async',
    'build_sink_async_factory', 'sink_async_property'
]
