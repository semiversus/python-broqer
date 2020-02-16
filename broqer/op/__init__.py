""" The op module contains all operators broqer offers """

# synchronous operators
from broqer.op.combine_latest import CombineLatest, build_combine_latest
from broqer.op.filter_ import Filter, FilterTrue, FilterFalse, build_filter
from broqer.op.map_ import Map, build_map

# utils
from broqer.op.operator import OperatorConcat

# enable operator overloading
from .operator_overloading import apply_operator_overloading, Str, Bool, Int, \
    Float, Repr, Len, In, All, Any, BitwiseAnd, BitwiseOr

apply_operator_overloading()

__all__ = [
    'CombineLatest',
    'Filter', 'Map', 'FilterTrue',
    'FilterFalse', 'build_map', 'build_combine_latest',
    'build_filter', 'OperatorConcat', 'Str', 'Bool', 'Int',
    'Float', 'Repr',
    'Len', 'In', 'All', 'Any', 'BitwiseAnd', 'BitwiseOr',
]
