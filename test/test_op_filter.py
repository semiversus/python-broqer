import pytest

from broqer.op import Filter

from .helper import check_single_operator, NONE

@pytest.mark.parametrize('args, kwargs, input_vector, output_vector', [
    ((lambda v:v==0,), {}, (1, 2, 0, 0.0, None), (NONE, NONE, 0, 0.0, NONE)),
    ((), {'predicate': lambda v:v==0}, (1, 2, 0, 0.0, None), (NONE, NONE, 0, 0.0, NONE)),
    ((lambda v,a:v==a, 0), {}, (1, 2, 0, 0.0, None), (NONE, NONE, 0, 0.0, NONE)),
    ((lambda v,a:v==a, 1), {}, (1, 2, 0, 0.0, None), (1, NONE, NONE, NONE, NONE)),
    ((), {}, (1, 2, 0, 0.0, None, True, False, []), (1, 2, NONE, NONE, NONE, True, NONE, NONE)),

])
def test_with_publisher(args, kwargs, input_vector, output_vector):
    check_single_operator(Filter, args, kwargs, input_vector, output_vector)