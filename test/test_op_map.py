import pytest
from unittest import mock

from broqer import NONE, StatefulPublisher
from broqer.op import Map, Sink, build_map

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

@pytest.mark.parametrize('build_kwargs, init_args, init_kwargs, ref_args, ref_kwargs, exception', [
    (None, (), {}, (), {}, None),
    ({'unpack':True}, (), {}, (), {'unpack':True}, None),
    (None, (), {'unpack':True}, (), {'unpack':True}, TypeError),
    ({'unpack':False}, (), {}, (), {'unpack':False}, None),
    ({'unpack':False}, (), {'unpack':False}, (), {'unpack':False}, TypeError),
    (None, (1,), {'a':2}, (1,), {'unpack':False, 'a':2}, None),
    ({'unpack':True}, (1,), {'a':2}, (1,), {'unpack':True, 'a':2}, None),
    ({'unpack':False}, (1,), {'a':2}, (1,), {'unpack':False, 'a':2}, None),
    ({'foo':1}, (), {}, (), {}, TypeError),
])
def test_build(build_kwargs, init_args, init_kwargs, ref_args, ref_kwargs, exception):
    mock_cb = mock.Mock()
    ref_mock_cb = mock.Mock()

    try:
        if build_kwargs is None:
            dut = build_map(mock_cb)(*init_args, **init_kwargs)
        else:
            dut = build_map(**build_kwargs)(mock_cb)(*init_args, **init_kwargs)
    except Exception as e:
        assert isinstance(e, exception)
        return
    else:
        assert exception is None

    reference = Map(ref_mock_cb, *ref_args, **ref_kwargs)

    assert dut._unpack == reference._unpack

    v = StatefulPublisher((1,2))
    v | dut | Sink()
    v | reference | Sink()

    assert mock_cb.mock_calls == ref_mock_cb.mock_calls
    assert len(mock_cb.mock_calls) == 1