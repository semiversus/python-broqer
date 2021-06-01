"""

"""
import asyncio
from collections import deque
from enum import Enum
from typing import Any, Deque, Optional, Tuple  # noqa: F401

from broqer import NONE


class AsyncMode(Enum):
    """ AyncMode defines how to act when an emit happens while an scheduled
    coroutine is running """
    CONCURRENT = 1  # just run coroutines concurrent
    INTERRUPT = 2  # cancel running and call for new value
    QUEUE = 3  # queue the value(s) and call after coroutine is finished
    LAST = 4  # use last emitted value after coroutine is finished
    LAST_DISTINCT = 5  # like LAST but only when value has changed
    SKIP = 6  # skip values emitted during coroutine is running


class CoroQueue:
    def __init__(self, coro, mode=AsyncMode.CONCURRENT):
        self._coro = coro
        self._mode = mode

        # ._last_args is used for LAST_DISTINCT and keeps the last call argument
        self._last_args = None  # type: Optional[Tuple[Any]]

        # ._task is the reference to a running coroutine encapsulated as task
        self._task = None  # type: Optional[asyncio.Task]

        # queue is initialized with following sizes:
        # Mode:                size:
        # QUEUE                unlimited
        # LAST, LAST_DISTINCT  1
        # all others           no queue used
        self._queue = None  # type: Optional[Deque]

        if mode in (AsyncMode.QUEUE, AsyncMode.LAST, AsyncMode.LAST_DISTINCT):
            maxlen = (None if mode is AsyncMode.QUEUE else 1)
            self._queue = deque(maxlen=maxlen)

    def schedule(self, *args: Any) -> Optional[asyncio.Future]:
        # check if a coroutine is already running
        if self._task is not None:
            # append to queue if a queue is used in this mode
            if self._queue is not None:
                future = asyncio.Future()
                self._queue.append((future, args))
                return future

            # in SKIP mode just do nothin with this emit
            if self._mode is AsyncMode.SKIP:
                return None

            # cancel the future if INTERRUPT mode is used
            if self._mode is AsyncMode.INTERRUPT and not self._task.done():
                self._task.cancel()

        # start the coroutine
        future = asyncio.Future()
        self._start_task(future, args)

        return future

    def _start_task(self, future: asyncio.Future, args: Tuple[Any]):
        """ Start the coroutine as task """

        # when LAST_DISTINCT is used only start coroutine when value changed
        if self._mode is AsyncMode.LAST_DISTINCT and args == self._last_args:
            self._task = None
            future.set_result(NONE)
            return

        # store the value to be emitted for LAST_DISTINCT
        self._last_args = args

        # create a task out of it and add ._task_done as callback
        self._task = asyncio.ensure_future(self._run_task(args, future))

    async def _run_task(self, args: Tuple[Any], future: asyncio.Future):
        try:
            result = await self._coro(*args)
        except Exception as e:
            future.set_exception(e)
        else:
            future.set_result(result)

        if self._queue:
            future, arg = self._queue.popleft()

            # start the coroutine
            self._start_task(future, arg)
        else:
            self._task = None
