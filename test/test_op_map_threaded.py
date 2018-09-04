import asyncio
import time
import pytest

from broqer import NONE
from broqer.op import MapThreaded, MODE

from .helper import check_async_operator_coro

def add1(v, i=1):
    print('ADD', v, i)
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
    await check_async_operator_coro(MapThreaded, (map_thread, *args), {'mode':mode, **kwargs}, input_vector, output_vector, loop=event_loop)
    await asyncio.sleep(0.1)