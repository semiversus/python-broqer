from unittest import mock

from broqer import StatefulPublisher
from broqer.op import OperatorConcat, Map, Reduce, Sink

def test_operator_concat():
    DUT = OperatorConcat(Map(lambda v:v/2), Reduce(lambda s,v:s+v, init=0))
    mock_cb = mock.Mock()

    p = StatefulPublisher(0)

    p | DUT
    assert DUT.get() == 0

    DUT | Sink(mock_cb)

    for v in range(5):
        p.notify(v)

    mock_cb.assert_has_calls([mock.call(0), mock.call(0.5), mock.call(1.5), mock.call(3), mock.call(5)])

    assert DUT.get() == 5