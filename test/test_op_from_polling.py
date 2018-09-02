from unittest.mock import Mock, ANY
import itertools
import asyncio

import pytest

from broqer.op import FromPolling, sink
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

    disposable = dut | sink(mock)

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
    await asyncio.sleep(0.1)
    mock.assert_not_called()

    # resubscribe
    disposable = dut | sink(mock)

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
    dut | sink(mock)

    await asyncio.sleep(0.05)

    for result in result_vector[:-2]:
        mock.assert_called_once_with(result)
        mock.reset_mock()
        await asyncio.sleep(0.1)

    mock.assert_called_once_with(result_vector[-2])
    mock.reset_mock()

    mock2 = Mock()
    dut | sink(mock2)
    await asyncio.sleep(0.1)
    mock2.assert_called_once_with(result_vector[-1])

@pytest.mark.asyncio
async def test_errorhandler():
    mock = Mock(side_effect=ZeroDivisionError)
    mock_errorhandler = Mock()

    dut = FromPolling(0.1, lambda:0, error_callback=mock_errorhandler)
    dut | sink(mock)

    await asyncio.sleep(0.05)

    mock_errorhandler.assert_called_once_with(ZeroDivisionError, ANY, ANY)
    mock.assert_called_once_with(0)
