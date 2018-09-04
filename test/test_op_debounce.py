import pytest
from unittest import mock

from broqer import NONE
from broqer.op import Debounce

from .helper import check_async_operator_coro
from .eventloop import VirtualTimeEventLoop

@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

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
    ((0.1, False), ((0, True), (0.05, False), (0.1, True), (0.3, -1)), ((0, False), (0.2, True), (0.3, False), (0.4, -1))),
    ((0.1, True), ((0, False), (0.05, False), (0.10, False), (0.15, True), (0.2, True), (0.25, True)), ((0, True), (0.1, False), (0.15, True))), # retrigger
    ((0.1,), ((0, True), (0.15, True), (0.2, True), (0.25, False), (0.3, False)), ((0.1, True), (0.35, False))),
    ((0.1,), ((0, 0), (0.05, 1), (0.1, 1.0), (0.3, 2)), ((0.15, 1), (0.4, 2))),
])
@pytest.mark.asyncio
async def test_with_publisher(args, input_vector, output_vector, event_loop):
    init = args[1:] if args[1:] else None
    await check_async_operator_coro(Debounce, args, {}, input_vector, output_vector, has_state=True, loop=event_loop)

@pytest.mark.asyncio
async def test_debounce():
    import asyncio
    from broqer import default_error_handler, Publisher, op

    p = Publisher()
    mock_sink = mock.Mock()
    mock_error_handler = mock.Mock()

    default_error_handler.set(mock_error_handler)

    disposable = p | op.debounce(0.1) | op.sink(mock_sink)

    mock_sink.side_effect = ZeroDivisionError('FAIL')

    # test error_handler
    p.notify(1)
    mock_error_handler.assert_not_called()
    await asyncio.sleep(0.05)
    mock_error_handler.assert_not_called()
    await asyncio.sleep(0.1)
    mock_error_handler.assert_called_once_with(ZeroDivisionError, mock.ANY, mock.ANY)
    mock_sink.assert_called_once_with(1)

    mock_sink.reset_mock()

    # test unsubscribe
    p.notify(2)
    await asyncio.sleep(0.05)
    disposable.dispose()
    await asyncio.sleep(0.1)
    mock_sink.assert_not_called()

    # test reset
    mock_sink.reset_mock()
    debounce = p | op.debounce(0.1)
    disposable = debounce | op.sink(mock_sink)
    p.notify(1)
    await asyncio.sleep(0.05)
    debounce.reset()
    await asyncio.sleep(0.1)
    mock_sink.assert_not_called()

    disposable.dispose()

    # test reset again
    mock_sink.reset_mock()
    mock_sink.side_effect = None
    debounce = p | op.debounce(0, False)
    disposable = debounce | op.sink(mock_sink)
    p.notify(True)
    await asyncio.sleep(0.05)
    debounce.reset()
    mock_sink.assert_has_calls( (mock.call(False), mock.call(True), mock.call(False)) )

    # resubscribe
    mock_sink.reset_mock()
    p.notify(True)
    await asyncio.sleep(0.05)
    mock_sink.assert_called_once_with(True)

    disposable.dispose()

    debounce | op.sink()

    p.notify(True)

    await asyncio.sleep(0.05)

    assert debounce.get() == True
    await op.True_(debounce)
    mock_sink.assert_called_once_with(True)

