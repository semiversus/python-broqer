import pytest

from broqer.op import CombineLatest, Just

from .helper import check_multi_operator, NONE

@pytest.mark.parametrize('kwargs, input_vector, output_vector', [
    ({}, ((1,2), (NONE,3), (2,NONE), (2,3)), ((1,2),(1,3),(2,3),NONE)),
    ({}, ((1,), (2,), (2,), (3,)), ((1,2,NONE,3))),
    ({}, ((1,NONE,NONE,NONE), (NONE,2,NONE,NONE), (NONE,3,NONE,NONE), (NONE,NONE,4,5)), ((NONE,NONE,NONE,(1,3,4,5)))),
    ({'map_':lambda a,b:a+b}, ((1,1), (NONE, 2), (1, NONE), (NONE, -5)), (2, 3, NONE, -4)),
    ({'map_':lambda a,b:a>b}, ((1,1), (NONE, 2), (1, NONE), (NONE, -5)), (False, NONE, NONE, True)),
])
def test_with_publisher(kwargs, input_vector, output_vector):
    check_multi_operator(CombineLatest, kwargs, input_vector, output_vector, has_state=True)