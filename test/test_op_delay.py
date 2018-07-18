import pytest

from broqer.op import Delay

from .helper import check_async_operator_coro, NONE

@pytest.mark.parametrize('duration, input_vector, output_vector', [
    # repeated False followed by repeated True
    (0.01,
     ((0, False), (0.005, False), (0.010, False), (0.015, True), (0.02, True), (0.025, True)),
     ((0.01, False), (0.015, False), (0.020, False), (0.025, True), (0.03, True), (0.035, True))),

    # short glitches
    (0.01,
     ((0, False), (0.02, True), (0.025, False), (0.04, True), (0.06, False), (0.065, True)),
     ((0.01, False), (0.03, True), (0.035, False), (0.05, True), (0.07, False), (0.075, True))),

    # short glitches with 0 delay
    (0,
     ((0, False), (0.02, True), (0.025, False), (0.04, True), (0.06, False), (0.065, True)),
     ((0.0001, False), (0.02, True), (0.025, False), (0.04, True), (0.06, False), (0.065, True))),
     # ^-- have to fool check_async_operator_coro which is checking for 0 as really immediate

])
@pytest.mark.asyncio
async def test_with_publisher(duration, input_vector, output_vector, event_loop):
    await check_async_operator_coro(Delay, (duration,), {}, input_vector, output_vector, loop=event_loop)