import pytest

from broqer import Hub, Value
from broqer.utils import DatatypeCheck

def test_datatype_check():
    hub = Hub()
    datatype_check = DatatypeCheck(hub)

    value_int_meta = {'datatype': 'integer', 'minimum': '>value_untyped'}
    value_int = hub.assign('value_int', Value(0), meta=value_int_meta)
    value_untyped = hub.assign('value_untyped', Value(0))

    # check value_int
    assert datatype_check.cast('123', hub['value_int']) == 123
    assert datatype_check.cast(123.45, value_int) == 123
    assert datatype_check.cast(b'123', value_int) == 123

    assert datatype_check.check(123, value_int) is None
    # TODO: fix
    #with pytest.raises(ValueError):
    #    datatype_check.check(-100, value_int)

    # check value_untyped
    assert datatype_check.cast('123', value_untyped) == '123'
    assert datatype_check.cast(123.45, value_untyped) == 123.45
    assert datatype_check.cast(b'123', value_untyped) == b'123'

    assert datatype_check.check(123, value_untyped) is None
    assert datatype_check.check(-100, value_untyped) is None
