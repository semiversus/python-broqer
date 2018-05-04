from broqer import Subject
from broqer.op import cache, distinct, sink

import mock


def test_cache_distinct():
    s = Subject()
    cb = mock.Mock()

    dut = s | cache(0) | distinct()
    dut | sink(cb)

    cb.assert_called_once_with(0)
    assert dut.cache == 0

    cb.reset_mock()

    s.emit(0.0)
    assert dut.cache == 0
    cb.assert_not_called()

    s.emit(False)  # False == 0
    assert dut.cache == 0
    cb.assert_not_called()

    s.emit(1)
    assert dut.cache == 1
    cb.assert_called_once_with(1)

    s.emit(1, 2)
    assert dut.cache == (1, 2)
    cb.assert_called_with(1, 2)


def test_distinct():
    s = Subject()
    cb = mock.Mock()

    dut = s | distinct()
    dut | sink(cb)

    cb.assert_not_called()
    assert dut.cache is None

    s.emit(0.0)
    assert dut.cache == 0
    cb.assert_called_once_with(0)

    cb.reset_mock()

    s.emit(False)  # False == 0
    assert dut.cache == 0
    cb.assert_not_called()

    s.emit(1)
    assert dut.cache == 1
    cb.assert_called_once_with(1)
