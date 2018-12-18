from unittest.mock import Mock, ANY
import itertools
import asyncio

import pytest

from broqer.op import FromPolling, Sink
from .eventloop import VirtualTimeEventLoop

@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

@pytest.mark.asyncio
async def test_polling():
    mock = Mock()
    dut = FromPolling(0.1, itertools.count().__next__)

    with pytest.raises(ValueError):
        dut.get()

    disposable = dut | Sink(mock)

    mock.assert_called_once_with(0)

    mock.reset_mock()
    await asyncio.sleep(0.15)
    mock.assert_called_once_with(1)

    mock.reset_mock()
    await asyncio.sleep(0.1)
    mock.assert_called_once_with(2)

    # unsubscribe
    mock.reset_mock()
    disposable.dispose()
    await asyncio.sleep(0.3)
    mock.assert_not_called()

    # resubscribe
    disposable = dut | Sink(mock)

@pytest.mark.asyncio
async def test_cancel_on_unsubscribe():
    mock = Mock()
    dut = FromPolling(0.1, mock)

    disposable = dut | Sink()
    mock.assert_called_once()

    await asyncio.sleep(0.25)
    assert mock.call_count == 3

    disposable.dispose()
    await asyncio.sleep(0.3)
    assert mock.call_count == 3

@pytest.mark.asyncio
async def test_once():
    mock = Mock()
    err_mock = Mock()
    dut = FromPolling(None, mock, error_callback=err_mock)

    disposable = dut | Sink()
    mock.assert_called_once()

    await asyncio.sleep(0.25)
    assert mock.call_count == 1

    disposable.dispose()
    await asyncio.sleep(0.3)
    assert mock.call_count == 1
    err_mock.assert_not_called()

    mock.reset_mock()
    mock.side_effect = ValueError
    disposable = dut | Sink()
    assert mock.call_count == 1
    assert err_mock.call_count == 1


@pytest.mark.parametrize('args, kwargs, result_vector', [
    ((), {}, (1, 2, 3, 4, 5)),
    ((5,), {}, (5, 6, 7, 8, 9)),
    ((), {'offset':2}, (2, 3, 4, 5, 6)),
])
@pytest.mark.asyncio
async def test_with_args(args, kwargs, result_vector):
    counter = itertools.count()

    def poll(offset=1):
        return next(counter) + offset

    dut = FromPolling(0.1, poll, *args, **kwargs)
    mock = Mock()
    dut | Sink(mock)

    await asyncio.sleep(0.05)

    for result in result_vector[:-2]:
        mock.assert_called_once_with(result)
        mock.reset_mock()
        await asyncio.sleep(0.1)

    mock.assert_called_once_with(result_vector[-2])
    mock.reset_mock()

    mock2 = Mock()
    dut | Sink(mock2)
    await asyncio.sleep(0.1)
    mock2.assert_called_once_with(result_vector[-1])

@pytest.mark.asyncio
async def test_errorhandler():
    mock = Mock(side_effect=ZeroDivisionError)
    mock_errorhandler = Mock()

    dut = FromPolling(0.1, lambda:0, error_callback=mock_errorhandler)
    dut | Sink(mock)

    await asyncio.sleep(0.05)

    mock_errorhandler.assert_called_once_with(ZeroDivisionError, ANY, ANY)
    mock.assert_called_once_with(0)
