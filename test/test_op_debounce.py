import pytest

from broqer.op import Debounce

from .helper import check_async_operator_coro, NONE

@pytest.mark.parametrize('args, input_vector, output_vector', [
    # repeated False followed by repeated True
    ((0.1,),
     ((0, False), (0.05, False), (0.10, False), (0.15, True), (0.2, True), (0.25, True)),
     ((0.1, False), (0.25, True))),

    # same with retrigger False
    ((0.1, False),
     ((0, False), (0.05, False), (0.10, False), (0.15, True), (0.2, True), (0.25, True)),
     ((0, False), (0.25, True))),

    # same with retrigger True
    ((0.1, True),
     ((0, False), (0.05, False), (0.10, False), (0.15, True), (0.2, True), (0.25, True)),
     ((0, True), (0.10, False), (0.15, True))),

    # short glitches
    ((0.1,),
     ((0, False), (0.2, True), (0.25, False), (0.4, True), (0.6, False), (0.65, True)),
     ((0.1, False), (0.5, True))),

    # same with retrigger False
    ((0.1, False),
     ((0, False), (0.2, True), (0.25, False), (0.4, True), (0.6, False), (0.65, True)),
     ((0, False), (0.5, True), (0.6, False), (0.75, True))),

    # same with retrigger True
    ((0.1, True),
     ((0, False), (0.2, True), (0.25, False), (0.4, True), (0.6, False), (0.65, True)),
     ((0, True), (0.1, False), (0.2, True), (0.35, False), (0.4, True))),


    # various tests
    ((0.1,), ((0, True), (0.05, False), (0.1, True), (0.3, False)), ((0.2, True), (0.4, False))),
    ((0.1, False), ((0, True), (0.05, False), (0.1, True), (0.3, None)), ((0, False), (0.2, True), (0.3, False), (0.4, None))),
    ((0.1, True), ((0, False), (0.05, False), (0.10, False), (0.15, True), (0.2, True), (0.25, True)), ((0, True), (0.1, False), (0.15, True))), # retrigger
    ((0.1,), ((0, True), (0.15, True), (0.2, True), (0.25, False), (0.3, False)), ((0.1, True), (0.35, False))),
    ((0.1,), ((0, 0), (0.05, 1), (0.1, 1.0), (0.3, 2)), ((0.15, 1), (0.4, 2))),
])
@pytest.mark.asyncio
async def test_with_publisher(args, input_vector, output_vector, event_loop):
    init = args[1:] if args[1:] else None
    await check_async_operator_coro(Debounce, args, {}, input_vector, output_vector, has_state=True, loop=event_loop)