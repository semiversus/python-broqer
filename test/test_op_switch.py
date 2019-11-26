import pytest
from unittest import mock

from broqer import Publisher, NONE
from broqer.op import Switch, Sink

from .helper import check_single_operator

@pytest.mark.parametrize('mapping, kwargs, input_vector, output_vector', [
    ({0:Publisher('a'), 1:Publisher('b'), 2:Publisher('c')}, {}, (0, 1, 2, 2, 1, 3), ('a', 'b', 'c', NONE, 'b', ValueError)),
    ({'a':0, 'b':Publisher(1)}, {'default':2}, ('a', 'b', 'a', 'b', 'c', 'a', 'a', 'b'), (0, 1, 0, 1, 2, 0, NONE, 1)),
    (['No', 'Yes'], {'default':'Unknown'}, (False, True, 1, -1, -5, True, 5.8), ('No', 'Yes', NONE, NONE, 'Unknown', 'Yes', 'Unknown')),
    (['No', 'Yes'], {'default':'Unknown'}, (4, 0), ('Unknown', 'No')),
    (['No', 'Yes'], {}, (0, 4, 1), ('No', ValueError, 'Yes')),
])
def test_with_publisher(mapping, kwargs, input_vector, output_vector):
    check_single_operator(Switch, (mapping,), kwargs, input_vector, output_vector, has_state=None)


@pytest.mark.parametrize('subscribe_all', [True, False])
def test_subscribe_all(subscribe_all):
    p_select = Publisher('a')
    p1 = Publisher(0)
    p2 = Publisher(1)
    dut = Switch({'a': p1, 'b': p2, 'c': 2}, subscribe_all=subscribe_all)

    assert not p_select.subscriptions
    assert not p1.subscriptions
    assert not p2.subscriptions
    assert not dut.subscriptions

    mock_cb = mock.Mock()
    disposable = (p_select | dut).subscribe(Sink(mock_cb))

    assert len(dut.subscriptions) == 1
    assert len(p_select.subscriptions) == 1
    assert len(p1.subscriptions) == 1
    assert len(p2.subscriptions) == (1 if subscribe_all else 0)

    p_select.notify('b')

    assert len(dut.subscriptions) == 1
    assert len(p_select.subscriptions) == 1
    assert len(p1.subscriptions) == (1 if subscribe_all else 0)
    assert len(p2.subscriptions) == 1

    disposable.dispose()

    assert not p_select.subscriptions
    assert not p1.subscriptions
    assert not p2.subscriptions
    assert not dut.subscriptions