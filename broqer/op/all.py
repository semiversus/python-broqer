from .any import _MultiPredicate
from ._operator import build_operator


class All(_MultiPredicate):
    combination_operator = all  # type: ignore


all = build_operator(All)
