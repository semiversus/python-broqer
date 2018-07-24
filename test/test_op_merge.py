import pytest

from broqer.op import Merge

from .helper import check_multi_operator, NONE

@pytest.mark.parametrize('input_vector, output_vector', [
    (((1, NONE), (NONE, 2), (NONE, 3), (4, NONE)), (1, 2, 3, 4)),
])
def test_with_publisher(input_vector, output_vector):
    check_multi_operator(Merge, {}, input_vector, output_vector, has_state=None)
    # TODO: remove has_state=None
