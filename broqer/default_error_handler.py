import traceback


class DefaultErrorHandler:
    def __init__(self):
        self._error_callback = self._default_error_callback

    def _default_error_callback(self, exc_type, exc_value, exc_traceback):
        traceback.print_exception(exc_type, exc_value, exc_traceback)

    def __call__(self, exc_type, exc_value, exc_traceback):
        self._error_callback(exc_type, exc_value, exc_traceback)

    def set(self, error_callback):
        self._error_callback = error_callback


default_error_handler = DefaultErrorHandler()
