import pytest

from broqer import op, NONE, Value
from tests.helper_single import check_get_method, check_subscription, check_dependencies


def add(a, b, c, constant=0):
    return a + b * 2 + c * 3 + constant * 4


test_vector = [
    # o, args, kwargs, input_vector, output_vector
    (op.Map, (lambda v: v+1,), {}, [NONE, 1, 2], [NONE, 2, 3]),
    (op.Map, (lambda v: NONE,), {}, [1, 2], [NONE, NONE]),
    (op.Map, (), {'function': lambda v: v+1}, [NONE, 1, 2], [NONE, 2, 3]),
    (op.Map, (lambda a, b: a+b,), {'unpack': True}, [NONE, (1, 1), (2, 2)], [NONE, 2, 4]),
    (op.Map, (add, 1), {'unpack': True, 'constant': 2}, [NONE, (1, 1), (2, 2)], [NONE, 14, 19]),
    (op.build_map_factory(lambda v, o: v+o,), (1,), {}, [NONE, 1, 2], [NONE, 2, 3]),
    (op.build_map_factory(lambda a, b: a+b, unpack=True), (), {}, [(1, 1), (2, 2)], [2, 4]),
    (op.build_map_factory(unpack=True)(lambda a, b: a+b), (), {}, [(1, 1), (2, 2)], [2, 4]),
    (lambda: op.build_map(lambda v: v+1,), (), {}, [NONE, 1, 2], [NONE, 2, 3]),
    (lambda: op.build_map(unpack=False)(lambda v: v+1,), (), {}, [NONE, 1, 2], [NONE, 2, 3]),
]

@pytest.mark.parametrize('method', [check_get_method, check_subscription, check_dependencies])
@pytest.mark.parametrize('o,args,kwargs,input_vector,output_vector', test_vector)
def test_operator(method, o, args, kwargs, input_vector, output_vector):
    operator = o(*args, **kwargs)

    method(operator, input_vector, output_vector)


def test_map_factory_keyword():
    m = op.build_map_factory(lambda v: v+1)
    v = Value()
    with pytest.raises(TypeError, message='"unpack" has to be defined by decorator'):
        o = v | m(unpack=True)