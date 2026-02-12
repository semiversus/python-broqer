from unittest import mock
import asyncio

import pytest

from broqer.coro_queue import CoroQueue, AsyncMode, MaxQueueException
from broqer import NONE


@pytest.mark.parametrize('mode', AsyncMode)
@pytest.mark.parametrize('args', [(), (None,), (1, 2, 3)])
@pytest.mark.asyncio
async def test_simple_run(mode, args):
    excpected_result = args

    async def _coro(*args):
        await asyncio.sleep(0)
        return args

    coro_queue = CoroQueue(coro=_coro, mode=mode)

    # test the first call and wait for finish
    future = coro_queue.schedule(*args)
    assert (await future) == excpected_result

    if mode == AsyncMode.LAST_DISTINCT:
        # for LAST_DISTINCT, the following results will be broqer.NONE
        excpected_result = NONE

    # test a second time
    future = coro_queue.schedule(*args)
    assert (await future) == excpected_result

    await asyncio.sleep(0.001)

    # test a third time
    future = coro_queue.schedule(*args)
    assert (await future) == excpected_result


@pytest.mark.parametrize('mode', AsyncMode)
@pytest.mark.asyncio
async def test_exception(mode):
    async def _coro(fail):
        if fail:
            raise ZeroDivisionError()

    coro_queue = CoroQueue(coro=_coro, mode=mode)

    # test the first call and wait for finish
    future = coro_queue.schedule(True)
    with pytest.raises(ZeroDivisionError):
        await future

    # test a second time
    future = coro_queue.schedule(False)
    assert (await future) == None

    # test a third time
    future = coro_queue.schedule(True)
    with pytest.raises(ZeroDivisionError):
        await future


@pytest.mark.asyncio
async def test_concurrent():
    callback = mock.Mock()
    event = asyncio.Event()

    async def _coro(index):
        callback(f'Start {index}')
        await event.wait()
        callback(f'End {index}')
        return index

    coro_queue = CoroQueue(coro=_coro, mode=AsyncMode.CONCURRENT)

    # make two concurrent calls
    result1 = coro_queue.schedule(1)
    result2 = coro_queue.schedule(2)

    await asyncio.sleep(0)

    callback.assert_has_calls([mock.call('Start 1'), mock.call('Start 2')])
    callback.reset_mock()

    event.set()
    await asyncio.sleep(0.001)
    callback.assert_has_calls([mock.call('End 1'), mock.call('End 2')], any_order=True)

    assert result1.result() == 1
    assert result2.result() == 2

    # make a non-concurrent call
    event.set()
    assert (await coro_queue.schedule(3)) == 3


@pytest.mark.parametrize('wait', [True, False])
@pytest.mark.asyncio
async def test_interrupt(wait):
    callback = mock.Mock()
    event = asyncio.Event()

    async def _coro(index):
        callback(f'Start {index}')
        await event.wait()
        callback(f'End {index}')
        return index

    coro_queue = CoroQueue(coro=_coro, mode=AsyncMode.INTERRUPT)

    # make two concurrent calls, the first one will be interrupted (canceld)
    result1 = coro_queue.schedule(1)
    if wait:
        await asyncio.sleep(0.0001)
    result2 = coro_queue.schedule(2)

    await asyncio.sleep(0)

    callback.assert_called_with('Start 2')
    callback.reset_mock()

    event.set()
    await asyncio.sleep(0.001)
    callback.assert_called_once_with('End 2')

    assert result1.result() == NONE
    assert result2.result() == 2

    # make a non-concurrent call
    event.set()
    assert (await coro_queue.schedule(3)) == 3


@pytest.mark.asyncio
async def test_queue():
    callback = mock.Mock()
    event = asyncio.Event()

    async def _coro(index):
        callback(f'Start {index}')
        await event.wait()
        callback(f'End {index}')
        return index

    coro_queue = CoroQueue(coro=_coro, mode=AsyncMode.QUEUE)

    # make two concurrent calls
    result1 = coro_queue.schedule(1)
    result2 = coro_queue.schedule(2)

    await asyncio.sleep(0.001)
    event.set()
    event.clear()

    await asyncio.sleep(0.001)

    callback.assert_has_calls([mock.call('Start 1'), mock.call('End 1'), mock.call('Start 2')])

    assert result1.result() == 1
    assert not result2.done()

    callback.reset_mock()

    event.set()
    event.clear()
    await asyncio.sleep(0.001)

    callback.assert_called_once_with('End 2')

    # make a non-concurrent call
    event.set()
    assert (await coro_queue.schedule(3)) == 3


@pytest.mark.asyncio
async def test_queue_threshold():

    async def _coro(index):
        await asyncio.sleep(0.001)
        return index + 2

    coro_queue = CoroQueue(coro=_coro, mode=AsyncMode.QUEUE, max_queue_threshold=10)

    future_0 = coro_queue.schedule(0)
    future_1 = coro_queue.schedule(40)

    for index in range(10):
        coro_queue.schedule(index)

    with pytest.raises(MaxQueueException) as exc_info:
        await future_0

    assert str(exc_info.value) == 'CoroQueue size is 11 and exceeds 10'

    assert await future_1 == 42


@pytest.mark.parametrize('mode', AsyncMode)
@pytest.mark.asyncio
async def test_queue_threshold_wrong_mode(mode):

    if mode == AsyncMode.QUEUE:
        return

    async def _coro():
        await asyncio.sleep(0.001)
        return 42

    with pytest.raises(ValueError) as exc_info:
        CoroQueue(coro=_coro, mode=mode, max_queue_threshold=10)

    assert str(exc_info.value) == 'max_queue_threshold can only be used with mode=AsyncMode.QUEUE'


@pytest.mark.parametrize('distinct', [True, False])
@pytest.mark.asyncio
async def test_last(distinct):
    callback = mock.Mock()
    event = asyncio.Event()

    async def _coro(index):
        callback(f'Start {index}')
        await event.wait()
        callback(f'End {index}')
        return index

    mode = AsyncMode.LAST_DISTINCT if distinct else AsyncMode.LAST
    coro_queue = CoroQueue(coro=_coro, mode=mode)

    # make three concurrent calls
    result1 = coro_queue.schedule(1)
    result2 = coro_queue.schedule(2)
    result3 = coro_queue.schedule(1)

    await asyncio.sleep(0.001)
    event.set()
    await asyncio.sleep(0.001)

    expected_calls = [mock.call('Start 1'), mock.call('End 1')]

    if not distinct:
        expected_calls += [mock.call('Start 1'), mock.call('End 1')]

    callback.assert_has_calls(expected_calls)

    assert result1.result() == 1
    assert result2.result() == NONE
    assert result3.result() == (NONE if distinct else 1)

    # make a non-concurrent call
    event.set()
    assert (await coro_queue.schedule(3)) == 3


@pytest.mark.parametrize('wait', [True, False])
@pytest.mark.asyncio
async def test_skip(wait):
    callback = mock.Mock()
    event = asyncio.Event()

    async def _coro(index):
        callback(f'Start {index}')
        await event.wait()
        callback(f'End {index}')
        return index

    coro_queue = CoroQueue(coro=_coro, mode=AsyncMode.SKIP)

    # make two concurrent calls, the first one will be interrupted (canceld)
    result1 = coro_queue.schedule(1)
    if wait:
        await asyncio.sleep(0.0001)
    result2 = coro_queue.schedule(2)

    await asyncio.sleep(0)

    callback.assert_called_with('Start 1')
    callback.reset_mock()

    event.set()
    await asyncio.sleep(0.001)
    callback.assert_called_once_with('End 1')

    assert result1.result() == 1
    assert result2.result() == NONE

    # make a non-concurrent call
    event.set()
    assert (await coro_queue.schedule(3)) == 3