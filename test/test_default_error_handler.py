import pytest
import asyncio
from unittest.mock import Mock, ANY

from broqer import StatefulPublisher, Publisher, op, default_error_handler

from .helper import check_async_operator_coro, NONE
from .eventloop import VirtualTimeEventLoop

@pytest.yield_fixture()
def event_loop():
    loop = VirtualTimeEventLoop()
    yield loop
    loop.close()

async def _foo_coro(v):
    return v

@pytest.mark.parametrize('operator_cls, args', [
    (op.Debounce, (StatefulPublisher(True), 0)),
    (op.Delay, (StatefulPublisher(True), 0)),
    (op.MapAsync, (StatefulPublisher(True), _foo_coro)),
    # (op.MapThreaded, (StatefulPublisher(True), lambda v:None)), # run_in_executor is not implemented in VirtualTimeEventLoop
    (op.FromPolling, (0.1, lambda:None)),
    (op.Sample, (StatefulPublisher(True), 0.1)),
    (op.Throttle, (StatefulPublisher(True), 0.1)),
])
@pytest.mark.asyncio
async def test_errorhandler(operator_cls, args, capsys):
    mock = Mock(side_effect=ZeroDivisionError)

    # test default error handler
    dut = operator_cls(*args)
    dut | op.sink(mock)

    await asyncio.sleep(0.1)

    captured = capsys.readouterr()
    assert 'Traceback' in captured.err
    assert 'ZeroDivisionError' in captured.err

    # test custom default error handler
    mock_errorhandler = Mock()
    default_error_handler.set(mock_errorhandler)

    dut = operator_cls(*args)
    dut | op.sink(mock)

    await asyncio.sleep(0.1)

    mock_errorhandler.assert_called_with(ZeroDivisionError, ANY, ANY)

    default_error_handler.reset()

    # test custom error handler
    mock_errorhandler_custom = Mock()

    dut = operator_cls(*args, error_callback=mock_errorhandler_custom)
    dut | op.sink(mock)

    await asyncio.sleep(0.1)

    mock_errorhandler_custom.assert_called_with(ZeroDivisionError, ANY, ANY)

    default_error_handler.reset()
