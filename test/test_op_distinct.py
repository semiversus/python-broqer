import pytest
from broqer import Publisher, Subject
from broqer.op import distinct, sink, cache
import mock

def test_distinct():
  s=Subject()
  cb=mock.Mock()

  s|cache(0)|distinct()|sink(cb)

  cb.assert_called_once_with(0)
  cb.reset_mock()

  s.emit(0.0)
  cb.assert_not_called()