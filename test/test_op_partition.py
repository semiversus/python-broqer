import pytest
from unittest.mock import Mock

from broqer import Publisher, NONE
from broqer.op import Partition, Sink

from .helper import check_single_operator

@pytest.mark.parametrize('size, input_vector, output_vector', [
    (3, (0, 1, 2, 3, 4, 5, 6, 7), (NONE, NONE, (0, 1, 2) , NONE, NONE, (3, 4, 5))),
    (1, (0, 1, 2, 3, 4, 5, 6, 7), ((0,), (1,), (2,), (3,), (4,), (5,), (6,), (7,))),

])
def test_with_publisher(size, input_vector, output_vector):
    check_single_operator(Partition, (size,), {}, input_vector, output_vector, has_state=None)
    # TODO: remove has_state=None

def test_partition():
    mock = Mock()
    p = Publisher()

    dut = Partition(p,3)
    dut | Sink(mock)
    p.notify(1)
    p.notify(2)
    mock.assert_not_called()
    dut.flush()
    mock.assert_called_once_with((1,2))
