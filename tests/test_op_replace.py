import pytest

from broqer.op import Replace

from .helper import check_single_operator

@pytest.mark.parametrize('args, input_vector, output_vector', [
    ((0,), (1, 2, 3), (0, 0, 0)),
])
def test_with_publisher(args, input_vector, output_vector):
    check_single_operator(Replace, args, {}, input_vector, output_vector)