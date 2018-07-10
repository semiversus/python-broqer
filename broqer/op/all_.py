"""Applying any or all build in function to multiple publishers"""

from .any_ import _MultiPredicate
from ._operator import build_operator


class All(_MultiPredicate):
    """Applying all built in to source publishers"""
    combination_operator = all  # type: ignore


all_ = build_operator(All)  # pylint: disable=invalid-name
