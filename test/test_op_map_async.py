import asyncio

import pytest

from broqer.op import MapAsync, Mode

from .helper import check_async_operator_coro, NONE

async def add1(v, i=1):
    return v+i

async def wait(v, duration=0.015):
    await asyncio.sleep(duration)
    return v

@pytest.mark.parametrize('map_coro, args, kwargs, mode, input_vector, output_vector', [
    (add1, (), {}, Mode.CONCURRENT, ((0, 1), (0.01, 2), (0.02, 3)), ((0.001, 2), (0.01, 3), (0.02, 4))),
    (add1, (2,), {}, Mode.CONCURRENT, ((0, 1), (0.01, 2), (0.02, 3)), ((0.001, 3), (0.01, 4), (0.02, 5))),
    (add1, (), {'i':3}, Mode.CONCURRENT, ((0, 1), (0.01, 2), (0.02, 3)), ((0.001, 4), (0.01, 5), (0.02, 6))),
    (add1, (), {}, Mode.INTERRUPT, ((0, 1), (0.01, 2), (0.02, 3)), ((0.001, 2), (0.01, 3), (0.02, 4))),
    (add1, (), {}, Mode.QUEUE, ((0, 1), (0.01, 2), (0.02, 3)), ((0.001, 2), (0.01, 3), (0.02, 4))),
    (add1, (), {}, Mode.LAST, ((0, 1), (0.01, 2), (0.02, 3)), ((0.001, 2), (0.01, 3), (0.02, 4))),
    (add1, (), {}, Mode.LAST_DISTINCT, ((0, 1), (0.01, 2), (0.02, 3)), ((0.001, 2), (0.01, 3), (0.02, 4))),
    (add1, (), {}, Mode.SKIP, ((0, 1), (0.01, 2), (0.02, 3)), ((0.001, 2), (0.01, 3), (0.02, 4))),
    (wait, (), {}, Mode.CONCURRENT, ((0, 0), (0.005, 1), (0.01, 2), (0.02, 3)), ((0.015, 0), (0.02, 1), (0.025, 2), (0.035, 3))),
    (wait, (), {}, Mode.INTERRUPT, ((0, 0), (0.005, 1), (0.01, 2), (0.02, 3)), ((0.035, 3),)),
    (wait, (), {}, Mode.QUEUE, ((0, 0), (0.005, 1), (0.01, 2), (0.02, 3)), ((0.015, 0), (0.030, 1), (0.045, 2), (0.060, 3))),
    (wait, (), {}, Mode.LAST, ((0, 0), (0.005, 1), (0.01, 2), (0.02, 3)), ((0.015, 0), (0.03, 2), (0.045, 3))),
    (wait, (), {}, Mode.LAST_DISTINCT, ((0, 0), (0.005, 1), (0.01, 2), (0.02, 3)), ((0.015, 0), (0.03, 2), (0.045, 3))),
    (wait, (), {}, Mode.LAST_DISTINCT, ((0, 0), (0.005, 1), (0.01, 0), (0.02, 3)), ((0.015, 0), (0.035, 3))),
    (wait, (), {}, Mode.SKIP, ((0, 0), (0.005, 1), (0.01, 2), (0.02, 3)), ((0.015, 0), (0.035, 3))),
])
@pytest.mark.asyncio
async def test_with_publisher(map_coro, args, kwargs, mode, input_vector, output_vector, event_loop):
    await check_async_operator_coro(MapAsync, (map_coro, *args), {'mode':mode, **kwargs}, input_vector, output_vector, loop=event_loop)