import pytest

from broqer import Hub, op


def test_freeze():
    hub = Hub()
    hub['value1'] | op.sink()
    hub.assign('value2', op.Just(0))
    hub['value3'].emit(1)

    assert 'value1' in hub
    assert 'value2' in hub
    assert 'value3' in hub
    assert len(tuple(hub)) == 3

    hub.freeze()

    with pytest.raises(ValueError):
        hub['value4'] | op.sink()

    with pytest.raises(ValueError):
        hub.assign('value5', op.Just(0))

    with pytest.raises(ValueError):
        hub['value6'].emit(1)

    assert len(tuple(hub)) == 3

    hub.freeze(False)

    hub['value4'] | op.sink()
    hub.assign('value5', op.Just(0))
    hub['value6'].emit(1)

    assert 'value4' in hub
    assert 'value5' in hub
    assert 'value6' in hub
    assert len(tuple(hub)) == 6
