import pytest

from broqer.op import Debounce

from .helper import check_async_operator_coro, NONE

@pytest.mark.parametrize('args, input_vector, output_vector', [
    # repeated False followed by repeated True
    ((0.01,),
     ((0, False), (0.005, False), (0.010, False), (0.015, True), (0.02, True), (0.025, True)),
     ((0.01, False), (0.025, True))),

    # same with retrigger False
    ((0.01, False),
     ((0, False), (0.005, False), (0.010, False), (0.015, True), (0.02, True), (0.025, True)),
     ((0, False), (0.025, True))),

    # same with retrigger True
    ((0.01, True),
     ((0, False), (0.005, False), (0.010, False), (0.015, True), (0.02, True), (0.025, True)),
     ((0, True), (0.010, False), (0.015, True))),

    # various tests
    ((0.01,), ((0, True), (0.005, False), (0.01, True), (0.03, False)), ((0.02, True), (0.04, False))),
    ((0.01, False), ((0, True), (0.005, False), (0.01, True), (0.03, None)), ((0, False), (0.02, True), (0.03, False), (0.04, None))),
    ((0.01, True), ((0, False), (0.005, False), (0.010, False), (0.015, True), (0.02, True), (0.025, True)), ((0, True), (0.01, False), (0.015, True))), # retrigger
    ((0.01,), ((0, True), (0.015, True), (0.02, True), (0.025, False), (0.03, False)), ((0.01, True), (0.035, False))),
    ((0.01,), ((0, 0), (0.005, 1), (0.01, 1.0), (0.03, 2)), ((0.015, 1), (0.04, 2))),
])
@pytest.mark.asyncio
async def test_with_publisher(args, input_vector, output_vector, event_loop):
    init = args[1:] if args[1:] else None
    await check_async_operator_coro(Debounce, args, {}, input_vector, output_vector, initial_state=init, has_state=True, loop=event_loop)