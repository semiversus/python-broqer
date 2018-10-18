import asyncio
import time
import pytest
from unittest import mock

from broqer import NONE, StatefulPublisher
from broqer.op import MapThreaded, MODE, Sink, build_map_threaded

from .helper import check_async_operator_coro

def add1(v, i=1):
    print('ADD', v, i, v+i)
    return v+i

def wait(v, duration=0.15):
    time.sleep(duration)
    return v

@pytest.mark.parametrize('map_thread, args, kwargs, mode, input_vector, output_vector', [
    (add1, (), {}, MODE.CONCURRENT, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (add1, (2,), {}, MODE.CONCURRENT, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 3), (0.1, 4), (0.2, 5))),
    (add1, (), {'i':3}, MODE.CONCURRENT, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 4), (0.1, 5), (0.2, 6))),
    (add1, (), {}, MODE.QUEUE, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (add1, (), {}, MODE.LAST, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (add1, (), {}, MODE.LAST_DISTINCT, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (add1, (), {}, MODE.SKIP, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (wait, (), {}, MODE.CONCURRENT, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.15, 0), (0.2, 1), (0.25, 2), (0.35, 3))),
    (wait, (), {}, MODE.QUEUE, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.15, 0), (0.30, 1), (0.45, 2), (0.60, 3))),
    (wait, (), {}, MODE.LAST, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.15, 0), (0.3, 2), (0.45, 3))),
    (wait, (), {}, MODE.LAST_DISTINCT, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.15, 0), (0.3, 2), (0.45, 3))),
    (wait, (), {}, MODE.LAST_DISTINCT, ((0, 0), (0.05, 1), (0.1, 0), (0.2, 3)), ((0.15, 0), (0.35, 3))),
    (wait, (), {}, MODE.SKIP, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.15, 0), (0.35, 3))),
])
@pytest.mark.asyncio
async def test_with_publisher(map_thread, args, kwargs, mode, input_vector, output_vector, event_loop):
    error_handler = mock.Mock()

    await check_async_operator_coro(MapThreaded, (map_thread, *args), {'mode':mode, 'error_callback':error_handler, **kwargs}, input_vector, output_vector, loop=event_loop)
    await asyncio.sleep(0.2)
    error_handler.assert_not_called()

@pytest.mark.parametrize('build_kwargs, init_args, init_kwargs, ref_args, ref_kwargs, exception', [
    (None, (), {}, (), {}, None),
    (None, (), {'unpack':True}, (), {}, TypeError),
    ({'mode':MODE.LAST}, (), {}, (), {'mode':MODE.LAST}, None),
    ({'mode':MODE.LAST}, (), {'mode':MODE.QUEUE}, (), {'mode':MODE.QUEUE}, None),
    (None, (), {'mode':MODE.QUEUE}, (), {'mode':MODE.QUEUE}, None),
    (None, (1,2), {'mode':MODE.QUEUE, 'foo':3}, (1,2), {'mode':MODE.QUEUE, 'foo':3}, None),
    ({'mode':MODE.LAST, 'unpack':True}, (), {}, (), {'mode':MODE.LAST, 'unpack':True}, None),
])
def test_build(build_kwargs, init_args, init_kwargs, ref_args, ref_kwargs, exception):
    mock_cb = mock.Mock()
    ref_mock_cb = mock.Mock()

    try:
        if build_kwargs is None:
            dut = build_map_threaded(mock_cb)(*init_args, **init_kwargs)
        else:
            dut = build_map_threaded(**build_kwargs)(mock_cb)(*init_args, **init_kwargs)
    except Exception as e:
        assert isinstance(e, exception)
        return
    else:
        assert exception is None

    reference = MapThreaded(ref_mock_cb, *ref_args, **ref_kwargs)

    assert dut._options[1:] == reference._options[1:]  # don't compare coro

    v = StatefulPublisher((1,2))
    v | dut | Sink()
    v | reference | Sink()

    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.01))
    assert mock_cb.mock_calls == ref_mock_cb.mock_calls
    assert len(mock_cb.mock_calls) == 1

def test_argument_check():
    with pytest.raises(ValueError):
        MapThreaded(lambda v:v, mode=MODE.INTERRUPT)