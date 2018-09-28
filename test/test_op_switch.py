import pytest

from broqer import StatefulPublisher, NONE
from broqer.op import Switch

from .helper import check_single_operator

@pytest.mark.parametrize('mapping, kwargs, input_vector, output_vector', [
    ({0:StatefulPublisher('a'), 1:StatefulPublisher('b'), 2:StatefulPublisher('c')}, {}, (0, 1, 2, 2, 1, 3), ('a', 'b', 'c', NONE, 'b', ValueError)),
    ({'a':0, 'b':StatefulPublisher(1)}, {'default':2}, ('a', 'b', 'a', 'b', 'c', 'a', 'a', 'b'), (0, 1, 0, 1, 2, 0, NONE, 1)),
    (['No', 'Yes'], {'default':'Unknown'}, (False, True, 1, -1, -5, True, 5.8), ('No', 'Yes', NONE, NONE, 'Unknown', 'Yes', 'Unknown')),
    (['No', 'Yes'], {'default':'Unknown'}, (4, 0), ('Unknown', 'No')),
    (['No', 'Yes'], {}, (0, 4, 1), ('No', ValueError, 'Yes')),
])
def test_with_publisher(mapping, kwargs, input_vector, output_vector):
    check_single_operator(Switch, (mapping,), kwargs, input_vector, output_vector, has_state=None)
