import pytest
import operator

from broqer import Publisher, to_args
from broqer.op import Reduce

from .helper import check_single_operator, NONE

@pytest.mark.parametrize('func, init, input_vector, output_vector', [
    (lambda a,b:a+b, 0, (1, 2, 3), (1, 3, 6)),
    (operator.add, 0, (1, 2, 3), (1, 3, 6)),
    (operator.mul, 1, (1, 2, 3), (1, 2, 6)),
])
def test_with_publisher(func, init, input_vector, output_vector):
    check_single_operator(Reduce, (func, init), {}, input_vector, output_vector, has_state=True)