import pytest
from unittest import mock

from broqer.op import Throttle

from .helper import check_async_operator_coro, NONE
from .eventloop import VirtualTimeEventLoop

@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

@pytest.mark.parametrize('args, input_vector, output_vector', [
    # repeated False followed by repeated True
    ((0.1,),
     ((0, 0), (0.05, 1), (0.15, 2), (0.4, 3), (0.45, 5)),
     ((0.001, 0), (0.1, 1), (0.2, 2), (0.4, 3), (0.5, 5))),

])
@pytest.mark.asyncio
async def test_with_publisher(args, input_vector, output_vector, event_loop):
    init = args[1:] if args[1:] else None
    await check_async_operator_coro(Throttle, args, {}, input_vector, output_vector, has_state=True, loop=event_loop)

@pytest.mark.asyncio
async def test_throttle():
    import asyncio
    from broqer import default_error_handler, Publisher, op

    p = Publisher()
    mock_sink = mock.Mock()
    mock_error_handler = mock.Mock()

    default_error_handler.set(mock_error_handler)

    disposable = p | op.throttle(0.1) | op.sink(mock_sink)

    mock_sink.side_effect = (None, ZeroDivisionError('FAIL'))

    # test error_handler
    p.notify(1)
    await asyncio.sleep(0.05)
    mock_sink.assert_called_once_with(1)
    p.notify(2)
    await asyncio.sleep(0.1)
    mock_error_handler.assert_called_once_with(ZeroDivisionError, mock.ANY, mock.ANY)

    mock_sink.reset_mock()

    # test unsubscribe
    p.notify(2)
    mock_sink.reset_mock()
    await asyncio.sleep(0.05)
    disposable.dispose()
    await asyncio.sleep(0.1)
    mock_sink.assert_called_once_with(2)

    # test reset
    mock_sink.reset_mock()
    mock_sink.side_effect = None
    throttle = p | op.throttle(0.1)
    disposable = throttle | op.sink(mock_sink)
    p.notify(1)
    mock_sink.reset_mock()
    await asyncio.sleep(0.05)
    throttle.reset()
    p.notify(2)
    await asyncio.sleep(0.05)
    mock_sink.assert_called_once_with(2)

    disposable.dispose()

    # test reset again
    mock_sink.reset_mock()
    mock_sink.side_effect = None
    throttle = p | op.throttle(0.1)
    disposable = throttle | op.sink(mock_sink)

    # resubscribe
    mock_sink.reset_mock()
    p.notify(1)
    await asyncio.sleep(0.05)
    mock_sink.assert_called_once_with(1)

    disposable.dispose()

    throttle | op.sink()

    p.notify(2)
    await asyncio.sleep(0.05)
    p.notify(3)

    with pytest.raises(ValueError):
        throttle.get()
    assert await throttle == 3
    mock_sink.assert_called_once_with(1)

    # reset when nothing is to be emitted
    disposable = throttle | op.sink(mock_sink)
    mock_sink.reset_mock()
    await asyncio.sleep(0.15)

    throttle.reset()
    p.notify(4)
    mock_sink.assert_called_once_with(4)



