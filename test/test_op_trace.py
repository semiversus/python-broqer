from unittest import mock
import pytest

from broqer import Publisher, Hub, Subject
from broqer.op import Cache, Trace
from broqer.subject import Subject

@pytest.mark.parametrize('label', [None, 'foo'])
def test_trace(label, capsys):
    p = Publisher()
    if label is None:
        p | Trace()
    else:
        p | Trace(label=label)

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

def test_trace_topic(capsys):
    hub = Hub()
    hub['foo'].assign(Subject())

    mock_handler = mock.Mock()
    hub['foo'] | Trace(mock_handler)

    hub['foo'].emit('test')
    captured = capsys.readouterr()
    assert "Topic('foo') 'test'" in captured.out
