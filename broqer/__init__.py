# -*- coding: utf-8 -*-
""" Broqer is a carefully crafted library to operate with continuous streams
of data in a reactive style with publish/subscribe and broker functionality.
"""
from .default_error_handler import default_error_handler
from .types import NONE
from .disposable import Disposable, SubscriptionDisposable
from .publisher import Publisher, SubscriptionError
from .subscriber import Subscriber

from .value import Value

from .op import operator_overloading  # noqa: F401 enable operator overloading
from . import op

__author__ = 'Günther Jena'
__email__ = 'guenther@jena.at'
__version__ = '__version__ = 2.0.0-dev'

__all__ = [
    'Disposable', 'Publisher', 'Subscriber',
    'SubscriptionDisposable', 'SubscriptionError', 'NONE',
    'Value', 'default_error_handler', 'op'
]
