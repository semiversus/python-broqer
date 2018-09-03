import pytest

from broqer.op import Any
from broqer import StatefulPublisher

from .helper import check_single_operator, NONE

@pytest.mark.parametrize('args, kwargs, input_vector, output_vector', [
    ((), {}, (False, False, True, False), (False, NONE, True, False)),
    ((), {'predicate':lambda v:v}, (False, False, True, False), (False, NONE, True, False)),
    ((), {'predicate':lambda v:v>0}, (0, -1, 1, 2, 0), (False, NONE, True, NONE, False)),
    ((StatefulPublisher(True),), {}, (False, False, True, False), (True, NONE, NONE, NONE)),
    ((StatefulPublisher(True),), {'predicate':lambda v:v}, (False, False, True, False), (True, NONE, NONE, NONE)),
    ((StatefulPublisher(1),), {'predicate':lambda v:v>0}, (0, -1, 1, 2, 0), (True, NONE, NONE, NONE)),
    ((StatefulPublisher(False),), {}, (False, False, True, False), (False, NONE, True, False)),
    ((StatefulPublisher(False),), {'predicate':lambda v:v}, (False, False, True, False), (False, NONE, True, False)),
    ((StatefulPublisher(-1),), {'predicate':lambda v:v>0}, (0, -1, 1, 2, 0), (False, NONE, True, NONE, False)),
])
def test_with_publisher(args, kwargs, input_vector, output_vector):
    check_single_operator(Any, args, kwargs, input_vector, output_vector, has_state=True)