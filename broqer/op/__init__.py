""" The op module contains all operators broqer offers """

# synchronous operators
from broqer.op.combine_latest import CombineLatest, build_combine_latest
from broqer.op.filter_ import Filter, EvalTrue, EvalFalse, build_filter, \
                              build_filter_factory
from broqer.op.map_ import Map, build_map, build_map_factory
from broqer.op.map_async import MapAsync, build_map_async, \
                                build_map_async_factory, AsyncMode
from broqer.op.bitwise import BitwiseCombineLatest, map_bit

# utils
from broqer.op.concat import Concat

# enable operator overloading
from .py_operators import Str, Bool, Int, Float, Repr, Len, In, All, Any, \
                         BitwiseAnd, BitwiseOr, Not

__all__ = [
    'CombineLatest', 'BitwiseCombineLatest',
    'Filter', 'Map', 'EvalTrue', 'MapAsync', 'build_map_async', 'AsyncMode',
    'EvalFalse', 'build_map', 'build_map_factory', 'build_combine_latest',
    'build_filter', 'build_filter_factory', 'Concat', 'Str', 'Bool', 'Int',
    'Float', 'Repr', 'map_bit', 'build_map_async_factory',
    'Len', 'In', 'All', 'Any', 'BitwiseAnd', 'BitwiseOr', 'Not'
]
