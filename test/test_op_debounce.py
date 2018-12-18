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
     ((0, False), (0.2, True), (0.25, False), (0.4, True), (0.6, False), (0.65, True), (0.7, False)),
     ((0.1, False), (0.5, True), (0.8, False))),

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

    ((0.1, False), ((0, True), (0.01, True), (0.2, False), (0.21, True), (0.22, True)), ((0, False), (0.1, True), (0.2, False), (0.31, True))),
])
@pytest.mark.asyncio
async def test_with_publisher(args, input_vector, output_vector, event_loop):
    error_handler = mock.Mock()
    init = args[1:] if args[1:] else None
    await check_async_operator_coro(Debounce, args, {'error_callback':error_handler}, input_vector, output_vector, has_state=True, loop=event_loop)
    error_handler.assert_not_called()

@pytest.mark.asyncio
async def test_debounce():
    import asyncio
    from broqer import default_error_handler, Publisher, op

    p = Publisher()
    mock_sink = mock.Mock()
    mock_error_handler = mock.Mock()

    default_error_handler.set(mock_error_handler)

    disposable = p | op.Debounce(0.1) | op.Sink(mock_sink)

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
    debounce = p | op.Debounce(0.1)
    disposable = debounce | op.Sink(mock_sink)
    p.notify(1)
    await asyncio.sleep(0.05)
    debounce.reset()
    await asyncio.sleep(0.1)
    mock_sink.assert_not_called()

    disposable.dispose()

    # test reset again
    mock_sink.reset_mock()
    mock_sink.side_effect = None
    debounce = p | op.Debounce(0, False)
    disposable = debounce | op.Sink(mock_sink)
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

    debounce | op.Sink()

    p.notify(True)

    await asyncio.sleep(0.05)

    assert debounce.get() == True
    await debounce | op.True_()
    mock_sink.assert_called_once_with(True)

    # test argument check
    with pytest.raises(ValueError):
        op.Debounce(-1)

