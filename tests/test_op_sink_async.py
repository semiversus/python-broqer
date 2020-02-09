import asyncio

import pytest
from unittest import mock

from broqer import NONE, default_error_handler, Publisher
from broqer.op import SinkAsync, MODE, build_sink_async

from .helper import check_async_operator_coro
from .eventloop import VirtualTimeEventLoop

@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

async def add1(v, i=1):
    return v+i

async def wait(v, duration=0.15):
    await asyncio.sleep(duration)
    return v

async def foo_vargs(a, b, c):
    await asyncio.sleep(0.15)
    return a + b + c

async def _filter(a, b):
    return NONE if a>b else a+b

@pytest.mark.asyncio
async def test_sink_async():
    p = Publisher()
    mock_error_handler = mock.Mock()

    default_error_handler.set(mock_error_handler)

    # test error_handler for map coroutine
    async def _fail(v):
        raise ValueError()

    p2 = Publisher()
    disposable = p2 | SinkAsync(_fail)
    p2.notify(2)

    await asyncio.sleep(0.01)

    print(mock_error_handler.mock_calls)
    mock_error_handler.assert_called_once_with(ValueError, mock.ANY, mock.ANY)


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

    async def mock_cb_coro(*args, **kwargs):
        mock_cb(*args, **kwargs)

    async def ref_mock_cb_coro(*args, **kwargs):
        ref_mock_cb(*args, **kwargs)

    try:
        if build_kwargs is None:
            dut = build_sink_async(mock_cb_coro)(*init_args, **init_kwargs)
        else:
            dut = build_sink_async(**build_kwargs)(mock_cb_coro)(*init_args, **init_kwargs)
    except Exception as e:
        assert isinstance(e, exception)
        return
    else:
        assert exception is None

    reference = SinkAsync(ref_mock_cb_coro, *ref_args, **ref_kwargs)

    assert dut._map_async._options[1:] == reference._map_async._options[1:]  # don't compare coro

    v = Publisher((1,2))
    v.subscribe(dut)
    v.subscribe(reference)

    asyncio.get_event_loop().run_until_complete(asyncio.sleep(0.01))
    assert mock_cb.mock_calls == ref_mock_cb.mock_calls
    assert len(mock_cb.mock_calls) == 1
