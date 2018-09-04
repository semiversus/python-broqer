import pytest

from broqer import StatefulPublisher, NONE
from broqer.op import Switch

from .helper import check_single_operator

@pytest.mark.parametrize('mapping, input_vector, output_vector', [
    ({0:StatefulPublisher('a'), 1:StatefulPublisher('b'), 2:StatefulPublisher('c')}, (0, 1, 2, 2, 1), ('a', 'b', 'c', NONE, 'b'))
])
def test_with_publisher(mapping, input_vector, output_vector):
    check_single_operator(Switch, (mapping,), {}, input_vector, output_vector, has_state=None)
