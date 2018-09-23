import pytest
import operator
from unittest import mock

from broqer import Publisher, NONE, StatefulPublisher
from broqer.op import Reduce, build_reduce, Sink

from .helper import check_single_operator

@pytest.mark.parametrize('func, init, input_vector, output_vector', [
    (lambda a,b:a+b, 0, (1, 2, 3), (1, 3, 6)),
    (operator.add, 0, (1, 2, 3), (1, 3, 6)),
    (operator.mul, 1, (1, 2, 3), (1, 2, 6)),
])
def test_with_publisher(func, init, input_vector, output_vector):
    check_single_operator(Reduce, (func, init), {}, input_vector, output_vector, has_state=True)

@pytest.mark.parametrize('build_kwargs, init_args, init_kwargs, ref_args, ref_kwargs, exception', [
    (None, (), {}, (), {}, TypeError),
    (None, (), {'init':0}, (0,), {}, None),
    (None, (0,), {}, (), {'init':0}, None),
    ({'init':0}, (), {}, (), {'init':0}, None),
    ({'init':0}, (1,), {}, (), {'init':1}, None),
    ({'init':0}, (), {'init':1}, (), {'init':1}, None),
    ({'foo':0}, (), {}, (), {'init':0}, TypeError),
    (None, (), {'foo':3}, (), {'init':0}, TypeError),
])
def test_build(build_kwargs, init_args, init_kwargs, ref_args, ref_kwargs, exception):
    mock_cb = mock.Mock(return_value=(0,0))
    ref_mock_cb = mock.Mock(return_value=(0,0))

    try:
        if build_kwargs is None:
            dut = build_reduce(mock_cb)(*init_args, **init_kwargs)
        else:
            dut = build_reduce(**build_kwargs)(mock_cb)(*init_args, **init_kwargs)
    except Exception as e:
        assert isinstance(e, exception)
        return
    else:
        assert exception is None

    reference = Reduce(ref_mock_cb, *ref_args, **ref_kwargs)

    assert dut._init == reference._init
    assert dut._state == reference._state
    assert dut._result == reference._result

    v = StatefulPublisher(1)
    v | dut | Sink()
    v | reference | Sink()

    assert mock_cb.mock_calls == ref_mock_cb.mock_calls
    assert len(mock_cb.mock_calls) == 1