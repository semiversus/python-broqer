from unittest.mock import Mock

import pytest

from broqer import Publisher, NONE
from broqer.op import SlidingWindow, sink

from .helper import check_single_operator

@pytest.mark.parametrize('size, emit_partial, input_vector, output_vector', [
    (3, False, (0, 1, 2, 3, 4, 5, 6), (NONE, NONE, (0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5), (4, 5, 6))),
    (3, True, (0, 1, 2, 3, 4, 5, 6), ((0,), (0,1), (0, 1, 2), (1, 2, 3), (2, 3, 4), (3, 4, 5), (4, 5, 6))),
    (1, False, (0, 1, 2, 3, 4, 5, 6), ((0,), (1,), (2,), (3,), (4,), (5,), (6,))),
    (1, True, (0, 1, 2, 3, 4, 5, 6), ((0,), (1,), (2,), (3,), (4,), (5,), (6,))),
])
def test_with_publisher(size, emit_partial, input_vector, output_vector):
    check_single_operator(SlidingWindow, (size, emit_partial), {}, input_vector, output_vector, has_state=None)
    # TODO: remove has_state=None

def test_flush():
    p = Publisher()
    mock = Mock()

    dut = SlidingWindow(p, 3)
    dut | sink(mock)

    mock.assert_not_called()
    p.notify(1)
    mock.assert_not_called()
    p.notify(2)
    mock.assert_not_called()
    dut.flush()
    mock.assert_called_once_with( (1,2) )

    mock.reset_mock()
    p.notify(1)
    p.notify(2)
    mock.assert_not_called()
    p.notify(3)
    mock.assert_called_once_with( (1,2,3) )

    dut.flush()
    mock.assert_called_once_with( (1,2,3) )



