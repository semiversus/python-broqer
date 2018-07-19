import pytest

from broqer.op import Partition

from .helper import check_single_operator, NONE

@pytest.mark.parametrize('size, input_vector, output_vector', [
    (3, (0, 1, 2, 3, 4, 5, 6, 7), (NONE, NONE, (0, 1, 2) , NONE, NONE, (3, 4, 5))),
    (1, (0, 1, 2, 3, 4, 5, 6, 7), ((0,), (1,), (2,), (3,), (4,), (5,), (6,), (7,))),

])
def test_with_publisher(size, input_vector, output_vector):
    check_single_operator(Partition, (size,), {}, input_vector, output_vector, has_state=None)