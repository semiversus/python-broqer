""" Implementing DefaultErrorHandler. Object default_error_handler is used
as global object to register a callbacks for exceptions in asynchronous
operators, """
import traceback


def _default_error_callback(exc_type, exc_value, exc_traceback):
    """ Default error callback is printing traceback of the exception
    """
    traceback.print_exception(exc_type, exc_value, exc_traceback)


class DefaultErrorHandler:
    """ DefaultErrorHandler object is a callable which is calling a registered
    callback and is used for handling exceptions when asynchronous operators
    receiving an exception during .emit(). The callback can be registered via
    the .set(callback) method. The default callback is _default_error_callback
    which is dumping the traceback of the exception.
    """
    def __init__(self):
        self._error_callback = _default_error_callback

    def __call__(self, exc_type, exc_value, exc_traceback):
        """ When calling the call will be forwarded to the registered
        callback """
        self._error_callback(exc_type, exc_value, exc_traceback)

    def set(self, error_callback):
        """ Register a new callback

        :param error_callback: the callback to be registered
        """
        self._error_callback = error_callback

    def reset(self):
        """ Reset to the default callback (dumping traceback)
        """
        self._error_callback = _default_error_callback


default_error_handler = DefaultErrorHandler()  # pylint: disable=invalid-name
