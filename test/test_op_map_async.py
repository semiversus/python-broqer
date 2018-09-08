import asyncio

import pytest
from unittest import mock

from broqer import NONE
from broqer.op import MapAsync, MODE

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

@pytest.mark.parametrize('map_coro, args, kwargs, mode, input_vector, output_vector', [
    (add1, (), {}, MODE.CONCURRENT, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (add1, (2,), {}, MODE.CONCURRENT, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 3), (0.1, 4), (0.2, 5))),
    (add1, (), {'i':3}, MODE.CONCURRENT, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 4), (0.1, 5), (0.2, 6))),
    (add1, (), {}, MODE.INTERRUPT, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (add1, (), {}, MODE.QUEUE, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (add1, (), {}, MODE.LAST, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (add1, (), {}, MODE.LAST_DISTINCT, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (add1, (), {}, MODE.SKIP, ((0, 1), (0.1, 2), (0.2, 3)), ((0.01, 2), (0.1, 3), (0.2, 4))),
    (wait, (), {}, MODE.CONCURRENT, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.15, 0), (0.2, 1), (0.25, 2), (0.35, 3))),
    (wait, (), {}, MODE.INTERRUPT, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.35, 3),)),
    (wait, (), {}, MODE.QUEUE, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.15, 0), (0.30, 1), (0.45, 2), (0.60, 3))),
    (wait, (), {}, MODE.LAST, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.15, 0), (0.3, 2), (0.45, 3))),
    (wait, (), {}, MODE.LAST_DISTINCT, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.15, 0), (0.3, 2), (0.45, 3))),
    (wait, (), {}, MODE.LAST_DISTINCT, ((0, 0), (0.05, 1), (0.1, 0), (0.2, 3)), ((0.15, 0), (0.35, 3))),
    (wait, (), {}, MODE.SKIP, ((0, 0), (0.05, 1), (0.1, 2), (0.2, 3)), ((0.15, 0), (0.35, 3))),
    (foo_vargs, (), {'unpack':True}, MODE.QUEUE, ((0, (0, 0, 0)), (0.1, (0, 0, 1)), (0.2, (1, 0, 1))), ((0.15, 0), (0.3, 1), (0.45, 2))),
    (_filter, (), {'unpack':True}, MODE.CONCURRENT, ((0, (0,0)), (0.1, (0,1)), (0.2, (1,0)), (0.3, (1,1))), ((0.001, 0), (0.1, 1), (0.3, 2))),
])
@pytest.mark.asyncio
async def test_with_publisher(map_coro, args, kwargs, mode, input_vector, output_vector, event_loop):
    await check_async_operator_coro(MapAsync, (map_coro, *args), {'mode':mode, **kwargs}, input_vector, output_vector, has_state=None, loop=event_loop)
    await asyncio.sleep(0.3)

@pytest.mark.asyncio
async def test_map_async():
    import asyncio
    from broqer import default_error_handler, Publisher, op

    p = Publisher()
    mock_sink = mock.Mock()
    mock_error_handler = mock.Mock()

    default_error_handler.set(mock_error_handler)

    async def _map(v):
        return v

    disposable = p | op.map_async(_map) | op.sink(mock_sink)

    mock_sink.side_effect = ZeroDivisionError('FAIL')

    # test error_handler for notify
    p.notify(1)
    mock_error_handler.assert_not_called()
    await asyncio.sleep(0.01)
    mock_error_handler.assert_called_once_with(ZeroDivisionError, mock.ANY, mock.ANY)
    disposable.dispose()

    mock_error_handler.reset_mock()
    mock_sink.reset_mock()
    mock_sink.side_effect = None

    # test error_handler for map coroutine
    async def _fail(v):
        raise ValueError()

    p2 = Publisher()
    disposable = p2 | op.map_async(_fail) | op.sink(mock_sink)
    p2.notify(2)

    await asyncio.sleep(0.01)

    print(mock_error_handler.mock_calls)
    mock_error_handler.assert_called_once_with(ValueError, mock.ANY, mock.ANY)
    mock_sink.assert_not_called()