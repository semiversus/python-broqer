from unittest import mock
from itertools import product

import pytest

from broqer import Publisher, NONE, op, Sink
from tests.helper_multi import check_get_method, check_subscription, check_dependencies


test_vector = [
    # o, args, kwargs, input_vector, output_vector
    (op.CombineLatest, (), {},
        ((1, 2), (NONE, 3), (2, NONE), (2, 3)),
        ((1, 2), (1, 3), (2, 3), (2, 3), (2, 3))),
    (op.CombineLatest, (), {},
        ((1,), (2,), (2,), (3,)),
        (((1,), (2,), (2,), (3,)))),
    (op.CombineLatest, (), {},
        ((1, NONE, NONE, NONE), (NONE, 2, NONE, NONE), (NONE, 3, NONE, NONE), (NONE, NONE, 4, 5)),
        ((NONE, NONE, NONE, (1, 3, 4, 5)))),
    (op.CombineLatest, (), {'map_': lambda a, b: a+b},
        ((1, 1), (NONE, 2), (1, NONE), (NONE, -5)),
        (2, 3, 3, -4)),
    (op.CombineLatest, (), {'map_': lambda a, b: a > b},
        ((1, 1), (NONE, 2), (1, NONE), (NONE, -5)),
        (False, False, False, True)),
    (op.CombineLatest, (), {'map_': lambda a, b: NONE if a > b else a - b},
        ((0, 0), (NONE, 1), (1, NONE), (NONE, 0), (0, NONE)),
        (0, -1, 0, NONE, 0)),
    (op.build_combine_latest(lambda a, b: a + b), (), {},
        ((1, 1), (NONE, 2), (1, NONE), (NONE, -5)),
        (2, 3, 3, -4)),
    (op.build_combine_latest(map_=lambda a, b: a + b), (), {},
        ((1, 1), (NONE, 2), (1, NONE), (NONE, -5)),
        (2, 3, 3, -4)),
    (lambda p1, p2, f: op.build_combine_latest()(f)(p1, p2), (lambda a, b: a + b,), {},
        ((1, 1), (NONE, 2), (1, NONE), (NONE, -5)),
        (2, 3, 3, -4)),
]
@pytest.mark.parametrize('method', [check_get_method, check_subscription, check_dependencies])
@pytest.mark.parametrize('o,args,kwargs,input_vector,output_vector', test_vector)
def test_operator(method, o, args, kwargs, input_vector, output_vector):
    operator = o(*(Publisher(v) for v in input_vector[0]), *args, **kwargs)

    method(operator, input_vector, output_vector)


@pytest.mark.parametrize('factory', [
    lambda p1, p2, p3, emit_on: op.CombineLatest(p1, p2, p3, emit_on=emit_on),
    lambda p1, p2, p3, emit_on: op.build_combine_latest(lambda *n: n, emit_on=emit_on)(p1, p2, p3),
    ])
@pytest.mark.parametrize('flags', list(product([False, True], repeat=3)))
def test_emit_on(factory, flags):
    m = mock.Mock()

    publishers = [Publisher(None) for i in range(3)]

    emit_on = [p for p, f in zip(publishers, flags) if f]
    if len(emit_on) == 0:
        emit_on = None
    elif len(emit_on) == 1:
        emit_on = emit_on[0]

    operator = factory(*publishers, emit_on=emit_on)
    operator.subscribe(Sink(m))

    result = [None] * 3

    if flags.count(True) == 0:
        flags = [True] * 3

    for i, f in enumerate(flags):
        m.reset_mock()

        result[i] = i

        publishers[i].notify(i)

        if f:
            m.assert_called_once_with(tuple(result))
        else:
            m.assert_not_called()

@pytest.mark.parametrize('subscribe', [True, False])
def test_unsubscibe(subscribe):
    m = mock.Mock()

    p1, p2 = Publisher(NONE), Publisher(NONE)

    operator = op.CombineLatest(p1, p2)

    if subscribe:
        operator.subscribe(Sink())

    assert operator.get() == NONE

    p1.notify(1)
    assert operator.get() == NONE

    p2.notify(2)
    assert operator.get() == (1, 2)
