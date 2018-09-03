import traceback


def _default_error_callback(exc_type, exc_value, exc_traceback):
    """ default error callback is printing traceback of the exception
    """
    traceback.print_exception(exc_type, exc_value, exc_traceback)


class DefaultErrorHandler:
    def __init__(self):
        self._error_callback = _default_error_callback

    def __call__(self, exc_type, exc_value, exc_traceback):
        self._error_callback(exc_type, exc_value, exc_traceback)

    def set(self, error_callback):
        self._error_callback = error_callback

    def reset(self):
        self._error_callback = _default_error_callback


default_error_handler = DefaultErrorHandler()  # pylint: disable=invalid-name
