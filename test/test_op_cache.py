import pytest

from broqer.op import Cache

from .helper import check_single_operator, NONE

@pytest.mark.parametrize('args, input_vector, output_vector', [
    ((-1,), (0, 1, 2, 3), (0, 1, 2, 3)),
    ((-1,), (-1, -1, -1, -1), (NONE, NONE, NONE, NONE)),
    ((-1,), (1, 1, -1, -1), (1, NONE, -1, NONE)),
    (('a',), (None, None, 'b', -1), (None, NONE, 'b', -1)),
    ((1,2), ((1,2), (1,3), (1,3)), (NONE, (1,3), NONE)),
])
def test_with_publisher(args, input_vector, output_vector):
    check_single_operator(Cache, args, {}, input_vector, output_vector, initial_state=args, has_state=True)