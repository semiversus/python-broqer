import pytest

from broqer import NONE
from broqer.op import Map

from .helper import check_single_operator

@pytest.mark.parametrize('args, kwargs, input_vector, output_vector', [
    ((lambda v:v+1,), {}, (0, 1, 2, 3), (1, 2, 3, 4)),
    ((lambda a,b:a+b, 1), {}, (0, 1, 2, 3), (1, 2, 3, 4)),
    ((lambda v:None,), {}, (0, 1, 2, 3), (None, None, None, None)),
    ((lambda a,b:a+b,), {'unpack':True}, ((0,0), (0,1), (1,0), (1,1)), (0, 1, 1, 2)),
    ((lambda a,b,c:a+b+c,1), {'unpack':True}, ((0,0), (0,1), (1,0), (1,1)), (1, 2, 2, 3)),
    ((lambda a,b,c:a+b+c,1), {'unpack':True}, ((0,0), (0,1), (1,0), (1,1)), (1, 2, 2, 3)),
    ((lambda a,b:NONE if a>b else a+b,), {'unpack':True}, ((0,0), (0,1), (1,0), (1,1)), (0, 1, NONE, 2)),

])
def test_with_publisher(args, kwargs, input_vector, output_vector):
    check_single_operator(Map, args, kwargs, input_vector, output_vector)
