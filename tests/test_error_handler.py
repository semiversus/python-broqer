import sys
from unittest.mock import Mock

import pytest

from broqer.error_handler import default_error_handler


def test_default(capsys):
    try:
        0/0
    except:
        exc = sys.exc_info()

    default_error_handler(*exc)

    captured = capsys.readouterr()

    assert captured.err.startswith('Traceback (most recent call last):')
    assert 'ZeroDivisionError: division by zero' in captured.err
    assert __file__ in captured.err

    assert captured.out == ''


def test_set_errorhandler(capsys):
    mock = Mock()
    default_error_handler.set(mock)

    try:
        0/0
    except:
        exc = sys.exc_info()

    default_error_handler(*exc)

    mock.assert_called_once_with(*exc)

    captured = capsys.readouterr()

    assert captured.err == ''
    assert captured.out == ''

    # reset
    default_error_handler.reset()

    default_error_handler(*exc)

    captured = capsys.readouterr()
    assert captured.err.startswith('Traceback (most recent call last):')
