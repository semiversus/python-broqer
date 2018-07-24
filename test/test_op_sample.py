import pytest

from broqer.op import Sample

from .helper import check_async_operator_coro, NONE

@pytest.mark.parametrize('interval, input_vector, output_vector', [
    (0.10,
     ((0, False), (0.25, True)),
     ((0, False), (0.1, False), (0.2, False), (0.3, True), (0.4, True))),
])
@pytest.mark.asyncio
async def test_with_publisher(interval, input_vector, output_vector, event_loop):
    await check_async_operator_coro(Sample, (interval,), {}, input_vector, output_vector, has_state=True, loop=event_loop)