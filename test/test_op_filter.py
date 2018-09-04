import pytest

from broqer import NONE
from broqer.op import Filter, True_, False_

from .helper import check_single_operator

@pytest.mark.parametrize('args, kwargs, input_vector, output_vector', [
    ((lambda v:v==0,), {}, (1, 2, 0, 0.0, None), (NONE, NONE, 0, 0.0, NONE)),
    ((), {'predicate': lambda v:v==0}, (1, 2, 0, 0.0, None), (NONE, NONE, 0, 0.0, NONE)),
    ((lambda v,a:v==a, 0), {}, (1, 2, 0, 0.0, None), (NONE, NONE, 0, 0.0, NONE)),
    ((lambda v,a:v==a, 1), {}, (1, 2, 0, 0.0, None), (1, NONE, NONE, NONE, NONE)),
    ((lambda a,b:a==b,), {'unpack':True}, ((0,0), (0,1), (1,0), (1,1)), ((0,0), NONE, NONE, (1,1))),
])
def test_with_publisher(args, kwargs, input_vector, output_vector):
    check_single_operator(Filter, args, kwargs, input_vector, output_vector)

@pytest.mark.parametrize('input_vector, output_vector', [
    (('abc', False, 1, 2, 0, True, 0.0, ''), ('abc', NONE, 1, 2, NONE, True, NONE, NONE)),
    ((False, True), (NONE, True)),
    ((True, False), (True, NONE)),
])
def test_true(input_vector, output_vector):
    check_single_operator(True_, (), {}, input_vector, output_vector)

@pytest.mark.parametrize('input_vector, output_vector', [
    (('abc', False, 1, 2, 0, True, 0.0, ''), (NONE, False, NONE, NONE, 0, NONE, 0.0, '')),
    ((False, True), (False, NONE)),
    ((True, False), (NONE, False)),
])
def test_false(input_vector, output_vector):
    check_single_operator(False_, (), {}, input_vector, output_vector)