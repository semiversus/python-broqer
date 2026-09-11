import asyncio
from unittest import mock

import pytest

from broqer.timer import Timer


@pytest.mark.asyncio
async def test_timer_calls_callback_after_timeout():
    callback = mock.Mock()
    timer = Timer(callback)

    timer.start(0.1)
    assert timer.is_running()
    callback.assert_not_called()

    await asyncio.sleep(0.05)
    callback.assert_not_called()

    await asyncio.sleep(0.1)
    callback.assert_called_once_with()
    assert not timer.is_running()


@pytest.mark.asyncio
async def test_timer_passes_arguments_to_callback():
    callback = mock.Mock()
    timer = Timer(callback)

    timer.start(0.1, args=(1, 2))

    await asyncio.sleep(0.15)
    callback.assert_called_once_with(1, 2)


@pytest.mark.asyncio
async def test_timer_zero_timeout_triggers_immediately():
    callback = mock.Mock()
    timer = Timer(callback)

    timer.start(0, args=('now',))

    # a timeout of 0 bypasses the event loop and calls the callback directly
    callback.assert_called_once_with('now')
    assert not timer.is_running()


@pytest.mark.asyncio
async def test_timer_restart_resets_timeout():
    callback = mock.Mock()
    timer = Timer(callback)

    timer.start(0.1)
    await asyncio.sleep(0.05)

    # restarting must cancel the pending handle, not add a second one
    timer.start(0.1)
    await asyncio.sleep(0.075)
    callback.assert_not_called()

    await asyncio.sleep(0.05)
    callback.assert_called_once_with()


@pytest.mark.asyncio
async def test_timer_cancel_prevents_callback():
    callback = mock.Mock()
    timer = Timer(callback)

    timer.start(0.1)
    timer.cancel()
    assert not timer.is_running()

    await asyncio.sleep(0.15)
    callback.assert_not_called()


@pytest.mark.asyncio
async def test_timer_change_arguments():
    callback = mock.Mock()
    timer = Timer(callback)

    timer.start(0.1, args=('old',))
    timer.change_arguments(args=('new',))

    await asyncio.sleep(0.15)
    callback.assert_called_once_with('new')


@pytest.mark.asyncio
async def test_timer_without_callback():
    timer = Timer()

    timer.start(0.1)
    await asyncio.sleep(0.05)
    assert timer.is_running()
    await asyncio.sleep(0.1)

    assert not timer.is_running()


@pytest.mark.asyncio
async def test_end_early_calls_callback_immediately():
    callback = mock.Mock()
    timer = Timer(callback)

    timer.start(0.1, args=('value',))
    callback.assert_not_called()
    assert timer.is_running()

    timer.end_early()

    callback.assert_called_once_with('value')
    assert not timer.is_running()


@pytest.mark.asyncio
async def test_end_early_cancels_pending_handle():
    """ Regression test: end_early() used to drop the handle without
    cancelling it, so the callback still fired at the original timeout. """
    callback = mock.Mock()
    timer = Timer(callback)

    timer.start(0.1)
    timer.end_early()
    callback.assert_called_once_with()

    # well past the original timeout - the callback must not fire a second time
    await asyncio.sleep(0.2)
    callback.assert_called_once_with()


@pytest.mark.asyncio
async def test_end_early_when_idle_is_noop():
    callback = mock.Mock()
    timer = Timer(callback)

    timer.end_early()

    callback.assert_not_called()
    assert not timer.is_running()


@pytest.mark.asyncio
async def test_end_early_twice_calls_callback_once():
    callback = mock.Mock()
    timer = Timer(callback)

    timer.start(0.1)
    timer.end_early()
    timer.end_early()

    callback.assert_called_once_with()


@pytest.mark.asyncio
async def test_end_early_without_callback():
    timer = Timer()

    timer.start(0.1)

    assert timer.is_running()
    timer.end_early()

    assert not timer.is_running()

    await asyncio.sleep(0.2)
    assert not timer.is_running()


@pytest.mark.asyncio
async def test_end_early_callback_may_restart_timer():
    """ The handle is cleared before the callback runs, so a callback that
    restarts the timer must not be clobbered. """
    timer_ref = []
    calls = []

    def callback(*args):
        calls.append(args)
        if len(calls) == 1:
            timer_ref[0].start(0.1, args=('restarted',))

    timer = Timer(callback)
    timer_ref.append(timer)

    timer.start(0.1, args=('first',))
    timer.end_early()

    assert calls == [('first',)]
    assert timer.is_running()

    await asyncio.sleep(0.15)
    assert calls == [('first',), ('restarted',)]
    assert not timer.is_running()
