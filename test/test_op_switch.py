import pytest

from broqer.op import Switch, Just

from .helper import check_single_operator, NONE

@pytest.mark.parametrize('mapping, input_vector, output_vector', [
    ({0:Just('a'), 1:Just('b'), 2:Just('c')}, (0, 1, 2, 2, 1), ('a', 'b', 'c', NONE, 'b'))
])
def test_with_publisher(mapping, input_vector, output_vector):
    check_single_operator(Switch, (mapping,), {}, input_vector, output_vector, has_state=None)
