import pytest
import asyncio
from unittest.mock import Mock, ANY

from broqer import Publisher, NONE
from broqer.op import Sample, Sink

from .helper import check_async_operator_coro
from .eventloop import VirtualTimeEventLoop

@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

@pytest.mark.parametrize('interval, input_vector, output_vector', [
    (0.10,
     ((0, False), (0.25, True)),
     ((0, False), (0.1, False), (0.2, False), (0.3, True), (0.4, True))),
])
@pytest.mark.asyncio
async def test_with_publisher(interval, input_vector, output_vector, event_loop):
    await check_async_operator_coro(Sample, (interval,), {}, input_vector, output_vector, has_state=True, loop=event_loop)

@pytest.mark.asyncio
async def test_sample():
    p = Publisher()
    dut = Sample(p, 0.1)

    mock = Mock()
    disposable = dut | Sink(mock)

    await asyncio.sleep(0.2)
    mock.assert_not_called()

    p.notify(1)
    mock.assert_called_once_with(1)
    mock.reset_mock()
    await asyncio.sleep(0.15)
    mock.assert_called_once_with(1)

    disposable.dispose()
    mock.reset_mock()
    await asyncio.sleep(0.2)
    mock.assert_not_called()

@pytest.mark.asyncio
async def test_errorhandler():
    mock = Mock(side_effect=ZeroDivisionError)
    mock_errorhandler = Mock()

    p = Publisher()

    dut = Sample(p, 0.1, error_callback=mock_errorhandler)
    dut | Sink(mock)

    p.notify(1)
    mock.assert_called_once_with(1)
    mock_errorhandler.assert_called_once_with(ZeroDivisionError, ANY, ANY)
