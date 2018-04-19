import mock
from broqer import Disposable
from broqer.op import Sink, sink, cache
from broqer.subject import Subject


def test_sink():
        cb = mock.Mock()

        s = Subject()
        sink_instance = Sink(s, cb)
        assert isinstance(sink_instance, Disposable)

        assert not cb.called
        assert len(s) == 1

        # test various emits on source
        s.emit()
        cb.assert_called_with()

        s.emit(None)
        cb.assert_called_with(None)

        s.emit(1)
        cb.assert_called_with(1)

        s.emit(1, 2)
        cb.assert_called_with(1, 2)

        s.emit((1, 2))
        cb.assert_called_with((1, 2))

        # testing dispose()
        cb.reset_mock()

        sink_instance.dispose()
        assert len(s) == 0

        s.emit(1)
        assert not cb.called


def test_sink_on_subscription():
        cb = mock.Mock()

        s = Subject()
        sink_instance = s | cache(0) | sink(cb)
        assert isinstance(sink_instance, Disposable)

        cb.assert_called_with(0)
        assert len(s) == 1

        s.emit(1)
        cb.assert_called_with(1)

        # testing dispose()
        cb.reset_mock()

        sink_instance.dispose()
        assert len(s) == 0

        s.emit(1)
        assert not cb.called


def test_sink_partial():
        cb = mock.Mock()

        s = Subject()
        sink_instance = Sink(s, cb, 1, 2, 3, a=1)
        assert isinstance(sink_instance, Disposable)

        assert not cb.called
        assert len(s) == 1

        # test various emits on source
        s.emit()
        cb.assert_called_with(1, 2, 3, a=1)

        s.emit(None)
        cb.assert_called_with(1, 2, 3, None, a=1)

        s.emit(1)
        cb.assert_called_with(1, 2, 3, 1, a=1)

        s.emit(1, 2)
        cb.assert_called_with(1, 2, 3, 1, 2, a=1)

        s.emit((1, 2))
        cb.assert_called_with(1, 2, 3, (1, 2), a=1)

        # testing dispose()
        cb.reset_mock()

        sink_instance.dispose()
        assert len(s) == 0

        s.emit(1)
        assert not cb.called
