import asyncio
import pytest
from unittest import mock

from broqer import NONE, Sink, Publisher, op
from broqer.op import Throttle


@pytest.mark.asyncio
async def test_throttle_errorhandler():
    from broqer import default_error_handler

    p = Publisher()
    mock_sink = mock.Mock()
    mock_error_handler = mock.Mock()

    default_error_handler.set(mock_error_handler)

    throttle = p | op.Throttle(0.1)
    disposable = throttle.subscribe(Sink(mock_sink))

    mock_sink.side_effect = (None, ZeroDivisionError('FAIL'))

    # test error_handler
    p.notify(1)
    await asyncio.sleep(0.05)
    mock_sink.assert_called_once_with(1)
    p.notify(2)
    await asyncio.sleep(0.1)
    mock_error_handler.assert_called_once_with(ZeroDivisionError, mock.ANY, mock.ANY)
    mock_sink.assert_has_calls((mock.call(1), mock.call(2)))

    mock_sink.reset_mock()


@pytest.mark.asyncio
async def test_throttle_unsubscribe():
    p = Publisher()
    mock_sink = mock.Mock()

    throttle = p | op.Throttle(0.1)
    disposable = throttle.subscribe(Sink(mock_sink))

    # test subscription and unsubscribe
    p.notify(2)
    mock_sink.assert_called_once_with(2)

    await asyncio.sleep(0.05)
    mock_sink.reset_mock()

    disposable.dispose()
    await asyncio.sleep(0.1)

    # dispose must not emit anything
    mock_sink.assert_not_called()

    p.notify(3)

    await asyncio.sleep(0.1)

    # after dispose was called, p.notify must not emit to mock_sink
    mock_sink.assert_not_called()


@pytest.mark.asyncio
async def test_throttle_reset():
    p = Publisher()
    mock_sink = mock.Mock()

    throttle = p | op.Throttle(0.1)
    disposable = throttle.subscribe(Sink(mock_sink))

    p.notify(1)
    await asyncio.sleep(0.05)
    throttle.reset()
    p.notify(3)

    await asyncio.sleep(0.05)

    # reset is called after "1" was emitted
    mock_sink.assert_has_calls((mock.call(1), mock.call(3)))

    ## wait until initial state is set and reset mock
    await asyncio.sleep(0.1)
    mock_sink.reset_mock()

    p.notify(1)
    await asyncio.sleep(0.05)
    p.notify(2)
    throttle.reset()
    p.notify(3)

    await asyncio.sleep(0.05)

    # reset is called after "1" was emitted, and while "2" was hold back,
    #   therefore "1" and "3" are emitted, but "2" is ignored
    mock_sink.assert_has_calls((mock.call(1), mock.call(3)))

    disposable.dispose()


@pytest.mark.parametrize('emit_sequence, expected_emits', [
    (((0, 0), (0.05, 1), (0.4, 2), (0.6, 3), (0.2, 4), (0.2, 5)),
     (mock.call(0), mock.call(2), mock.call(3), mock.call(5))),
    (((0.001, 0), (0.6, 1), (0.5, 2), (0.05, 3), (0.44, 4)),
     (mock.call(0), mock.call(1), mock.call(2), mock.call(4))),
])
@pytest.mark.asyncio
async def test_throttle(emit_sequence, expected_emits):
    p = Publisher()
    mock_sink = mock.Mock()

    throttle = p | op.Throttle(0.5)
    disposable = throttle.subscribe(Sink(mock_sink))

    mock_sink.assert_not_called()

    for item in emit_sequence:
        await asyncio.sleep(item[0])
        p.notify(item[1])

    await asyncio.sleep(0.5)

    mock_sink.assert_has_calls(expected_emits)


def test_argument_check():
    with pytest.raises(ValueError):
        Throttle(-1)
