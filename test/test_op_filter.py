import pytest
from unittest import mock

from broqer import NONE, StatefulPublisher, NONE
from broqer.op import Filter, True_, False_, build_filter, Sink

from .helper import check_single_operator

@pytest.mark.parametrize('args, kwargs, input_vector, output_vector', [
    ((lambda v:v==0,), {}, (1, 2, 0, 0.0, None), (NONE, NONE, 0, 0.0, NONE)),
    ((), {'predicate': lambda v:v==0}, (1, 2, 0, 0.0, None), (NONE, NONE, 0, 0.0, NONE)),
    ((lambda v,a:v==a, 0), {}, (1, 2, 0, 0.0, None), (NONE, NONE, 0, 0.0, NONE)),
    ((lambda v,a:v==a, 1), {}, (1, 2, 0, 0.0, None), (1, NONE, NONE, NONE, NONE)),
    ((lambda a,b:a==b,), {'unpack':True}, ((0,0), (0,1), (1,0), (1,1)), ((0,0), NONE, NONE, (1,1))),
])
def test_with_publisher(args, kwargs, input_vector, output_vector):
    check_single_operator(Filter, args, kwargs, input_vector, output_vector)

@pytest.mark.parametrize('input_vector, output_vector', [
    (('abc', False, 1, 2, 0, True, 0.0, ''), ('abc', NONE, 1, 2, NONE, True, NONE, NONE)),
    ((False, True), (NONE, True)),
    ((True, False), (True, NONE)),
])
def test_true(input_vector, output_vector):
    check_single_operator(True_, (), {}, input_vector, output_vector)

@pytest.mark.parametrize('input_vector, output_vector', [
    (('abc', False, 1, 2, 0, True, 0.0, ''), (NONE, False, NONE, NONE, 0, NONE, 0.0, '')),
    ((False, True), (False, NONE)),
    ((True, False), (NONE, False)),
])
def test_false(input_vector, output_vector):
    check_single_operator(False_, (), {}, input_vector, output_vector)

@pytest.mark.parametrize('build_kwargs, init_args, init_kwargs, ref_args, ref_kwargs, exception', [
    (None, (), {}, (), {}, None),
    (None, (), {'unpack':True}, (), {'unpack':True}, TypeError),
    (None, (), {'foo':True}, (), {'foo':True}, None),
    ({'unpack':True}, (), {}, (), {'unpack':True}, None),
    ({'unpack':False}, (), {}, (), {'unpack':False}, None),
    (None, (1,2,3), {'a':4}, (1,2,3), {'a':4}, None),
])
def test_build(build_kwargs, init_args, init_kwargs, ref_args, ref_kwargs, exception):
    mock_cb = mock.Mock()
    ref_mock_cb = mock.Mock()

    try:
        if build_kwargs is None:
            dut = build_filter(mock_cb)(*init_args, **init_kwargs)
        else:
            dut = build_filter(**build_kwargs)(mock_cb)(*init_args, **init_kwargs)
    except Exception as e:
        assert isinstance(e, exception)
        return
    else:
        assert exception is None

    reference = Filter(ref_mock_cb, *ref_args, **ref_kwargs)

    assert dut._unpack == reference._unpack

    v = StatefulPublisher((1,2))
    v | dut | Sink()
    v | reference | Sink()

    assert mock_cb.mock_calls == ref_mock_cb.mock_calls
    assert len(mock_cb.mock_calls) == 1