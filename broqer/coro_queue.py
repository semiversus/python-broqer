""" CoroQueue handles running a coroutine depending on a given mode
"""
import asyncio
from collections import deque
from enum import Enum
from typing import Any, Deque, Optional, Tuple  # noqa: F401
from functools import partial

from broqer import NONE


def wrap_coro(coro, unpack, *args, **kwargs):
    """ building a coroutine receiving one argument and call it curried
    with *args and **kwargs and unpack it (if unpack is set)
    """
    if unpack:
        async def _coro(value):
            return await coro(*args, *value, **kwargs)
    else:
        async def _coro(value):
            return await coro(*args, value, **kwargs)

    return _coro


class AsyncMode(Enum):
    """ AyncMode defines how to act when an emit happens while an scheduled
    coroutine is running """
    CONCURRENT = 1  # just run coroutines concurrent
    INTERRUPT = 2  # cancel running and call for new value
    QUEUE = 3  # queue the value(s) and call after coroutine is finished
    LAST = 4  # use last emitted value after coroutine is finished
    LAST_DISTINCT = 5  # like LAST but only when value has changed
    SKIP = 6  # skip values emitted during coroutine is running


class CoroQueue:  # pylint: disable=too-few-public-methods
    """ Schedules the running of a coroutine given on a mode
    :param coro: Coroutine to be scheduled
    :param mode: scheduling mode (see AsyncMode)
    """
    def __init__(self, coro, mode=AsyncMode.CONCURRENT):
        self._coro = coro
        self._mode = mode

        # ._last_args is used for LAST_DISTINCT and keeps the last arguments
        self._last_args = None  # type: Optional[Tuple]

        # ._task is the reference to a running coroutine encapsulated as task
        self._task = None  # type: Optional[asyncio.Future]

        # queue is initialized with following sizes:
        # Mode:                size:
        # QUEUE                unlimited
        # LAST, LAST_DISTINCT  1
        # all others           no queue used
        self._queue = \
            None  # type: Optional[Deque[Tuple[Tuple, asyncio.Future]]]

        if mode in (AsyncMode.QUEUE, AsyncMode.LAST, AsyncMode.LAST_DISTINCT):
            maxlen = (None if mode is AsyncMode.QUEUE else 1)
            self._queue = deque(maxlen=maxlen)

    def schedule(self, *args: Any) -> asyncio.Future:
        """ Schedule a coroutine run with the given arguments
        :param *args: variable length arguments
        """
        future = asyncio.Future()  # type: asyncio.Future

        # check if a coroutine is already running
        if self._task is not None:
            # append to queue if a queue is used in this mode
            if self._queue is not None:
                if self._queue.maxlen == 1 and len(self._queue) == 1:
                    _, queued_future = self._queue.popleft()
                    queued_future.set_result(NONE)

                self._queue.append((args, future))
                return future

            # in SKIP mode just do nothin with this emit
            if self._mode is AsyncMode.SKIP:
                future.set_result(NONE)
                return future

            # cancel the task if INTERRUPT mode is used
            if self._mode is AsyncMode.INTERRUPT and not self._task.done():
                self._task.cancel()

        # start the coroutine
        self._start_task(args, future)

        return future

    def _start_task(self, args: Tuple, future: asyncio.Future):
        """ Start the coroutine as task """

        # when LAST_DISTINCT is used only start coroutine when value changed
        if self._mode is AsyncMode.LAST_DISTINCT and args == self._last_args:
            self._task = None
            future.set_result(NONE)
            return

        # store the value to be emitted for LAST_DISTINCT
        self._last_args = args

        # create a task out of it and add ._task_done as callback
        self._task = asyncio.ensure_future(self._coro(*args))
        self._task.add_done_callback(partial(self._handle_done, future))

    def _handle_done(self, result_future: asyncio.Future, task: asyncio.Task):
        try:
            result = task.result()
        except asyncio.CancelledError:  # happend in INTERRUPT mode
            result_future.set_result(NONE)
        except Exception as exception:  # pylint: disable=broad-except
            result_future.set_exception(exception)
        else:
            result_future.set_result(result)

        if self._queue:
            args, future = self._queue.popleft()

            # start the coroutine
            self._start_task(args, future)
        else:
            self._task = None
