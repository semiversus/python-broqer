from unittest import mock
import pytest

from broqer import Publisher
from broqer.op import Trace

@pytest.mark.parametrize('label', [None, 'foo'])
def test_trace(label, capsys):
    p = Publisher()
    if label is None:
        p.subscribe(Trace())
    else:
        p.subscribe(Trace(label=label))

    captured = capsys.readouterr()
    assert captured.out == ''

    p.notify(3)
    captured = capsys.readouterr()
    assert '--- ' in captured.out
    assert ' 3'
    assert len(captured.out.splitlines()) == 1

    handler = mock.Mock()
    old_handler = Trace._trace_handler
    Trace.set_handler(handler)

    p.notify(4)

    handler.assert_called_once_with(p, 4, label=label)
    Trace._trace_handler = staticmethod(old_handler)  # restore handler
