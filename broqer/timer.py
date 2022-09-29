""" Asynchronous timer object """
import asyncio
from typing import Callable, Optional


class Timer:
    """ The timer object is used to have an abstraction for handling time
    dependend functionality. The timer works non-periodically.

    :param callback: an optional callback function called when the time
                     `timeout` has passed after calling `.start()` or when
                     calling `.end_early()`
    :param loop: optional asyncio event loop
    """
    def __init__(self, callback: Optional[Callable[[], None]] = None,
                 loop: Optional[asyncio.BaseEventLoop] = None):
        self._callback = callback
        self._handle = None  # type: Optional[asyncio.Handle]
        self._loop = loop or asyncio.get_running_loop()
        self._args = None

    def start(self, timeout: float, args=()) -> None:
        """ start the timer with given timeout. Optional arguments for the
        callback can be provided. When the timer is currently running, the
        timer will be re-set to the new timeout.

        :param timeout: time in seconds to the end of the timer
        :param args: optional tuple with arguments for the callback
        """
        if self._handle:
            self._handle.cancel()

        self._args = args

        if timeout > 0:
            self._handle = self._loop.call_later(timeout, self._trigger)
        else:
            self._trigger()

    def change_arguments(self, args=()):
        """ Will chance the arguments for the scheduled callback

        :param args: Positional arguments
        """
        self._args = args

    def cancel(self) -> None:
        """ Cancel the timer. An optional callback will not be called. """

        if self._handle:
            self._handle.cancel()
        self._handle = None

    def end_early(self) -> None:
        """ immediate stopping the timer and call optional callback """
        self._handle = None
        if self._handle and self._callback:
            self._callback(*self._args)

    def is_running(self) -> bool:
        """ tells if the timer is currently running
        :returns: boolean, True when timer is running
        """
        return self._handle is not None

    def _trigger(self):
        """ internal method called when timer is finished """
        self._handle = None
        if self._callback:
            self._callback(*self._args)
