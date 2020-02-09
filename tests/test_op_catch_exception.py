import pytest

from broqer import Publisher, Subscriber, NONE
from broqer.op import CatchException

from .helper import check_single_operator, Collector

@pytest.mark.parametrize('args, input_vector, output_vector', [
    ((ValueError,), (0, 1, 2, 3), (0, 1, 2, 3)),
])
def test_with_publisher(args, input_vector, output_vector):
    check_single_operator(CatchException, args, {}, input_vector, output_vector)

def test_exception():
    source = Publisher()
    dut = source | CatchException(ValueError)

    class _Subscriber(Subscriber):
        exception = None
        results = []

        def emit(self, arg, who: Publisher) -> None:
            if self.exception is not None:
                raise self.exception
            self.results.append(arg)

    subscriber = _Subscriber()
    dut.subscribe(subscriber)

    source.notify(1)
    source.notify(2)
    assert tuple(subscriber.results) == (1, 2)
    subscriber.exception = ValueError()
    source.notify(1)
    assert tuple(subscriber.results) == (1, 2)
    subscriber.exception = ZeroDivisionError()
    with pytest.raises(ZeroDivisionError):
        source.notify(3)

    with pytest.raises(ValueError):
        CatchException()