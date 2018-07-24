import pytest

from broqer.op import SlidingWindow

from .helper import check_single_operator, NONE

@pytest.mark.parametrize('size, emit_partial, input_vector, output_vector', [
    (3, False, (0, 1, 2, 3, 4, 5, 6), (NONE, NONE, (0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5), (4, 5, 6))),
    (3, True, (0, 1, 2, 3, 4, 5, 6), ((0,), (0,1), (0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5), (4, 5, 6))),
    (1, False, (0, 1, 2, 3, 4, 5, 6), ((0,), (1,), (2,), (3,), (4,), (5,), (6,))),
    (1, True, (0, 1, 2, 3, 4, 5, 6), ((0,), (1,), (2,), (3,), (4,), (5,), (6,))),
])
def test_with_publisher(size, emit_partial, input_vector, output_vector):
    check_single_operator(SlidingWindow, (size, emit_partial), {}, input_vector, output_vector, has_state=None)
    # TODO: remove has_state=None
