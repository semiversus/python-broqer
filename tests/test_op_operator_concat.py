from unittest import mock

from broqer import Publisher, NONE, Sink
from broqer.op import Concat, Map


def test_operator_concat():
    DUT = Concat(Map(lambda v: v/2), Map(lambda v: v+1))
    mock_cb = mock.Mock()

    p = Publisher()

    o = p | DUT
    assert o.get() == NONE

    p.notify(0)
    assert o.get() == 1.0

    o.subscribe(Sink(mock_cb))

    for v in range(5):
        p.notify(v)

    mock_cb.assert_has_calls(
        [mock.call(1.0), mock.call(1.5), mock.call(2.0), mock.call(2.5),
         mock.call(3.0)])

    assert o.get() == 3.0
