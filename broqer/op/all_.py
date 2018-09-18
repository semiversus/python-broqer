""" Applying any or all build in function to multiple publishers"""
from typing import Callable
from typing import Any as Any_

from broqer import Publisher

from .any_ import _MultiPredicate


class All(_MultiPredicate):
    """ Applying any built in to source publishers"""
    def __init__(self, *publishers: Publisher,
                 predicate: Callable[[Any_], bool] = None) -> None:
        _MultiPredicate.__init__(self, *publishers, predicate=predicate)
        self.combination_operator = all
