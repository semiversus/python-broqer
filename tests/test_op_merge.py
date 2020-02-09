import pytest

from broqer import NONE, Publisher
from broqer.op import Merge

from .helper import check_multi_operator

@pytest.mark.parametrize('input_vector, output_vector', [
    (((1, NONE), (NONE, 2), (NONE, 3), (4, NONE)), (1, 2, 3, 4)),
])
def test_with_publisher(input_vector, output_vector):
    check_multi_operator(Merge, {}, input_vector, output_vector, has_state=None)
    # TODO: remove has_state=None

def test_adding_publisher():
    p1 = Publisher()
    p2 = Publisher()
    dut = Merge(p1, p2)

    assert len(dut.source_publishers) == 2

    p3 = Publisher()
    p3 | dut

    assert len(dut.source_publishers) == 3
    assert p3 in dut.source_publishers
