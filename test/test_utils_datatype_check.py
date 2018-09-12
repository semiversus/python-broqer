import pytest
import types

from broqer import Hub, Subject, Value
from broqer.utils.datatype_check import DTRegistry, resolve_meta_key, DT

@pytest.mark.parametrize('meta,values,cast_results,check_results,str_results', [
    ({},
     (1, -1, True, None, 'abc', {'a':1.23}),
     (1, -1, True, None, 'abc', {'a':1.23}),
     (None, None, None, None, None, None),
     ('1', '-1', 'True', 'None', 'abc', '{\'a\': 1.23}')),
    ({'datatype': 'none'},
     (1, -1, True, None, 'abc', {'a':1.23}),
     (1, -1, True, None, 'abc', {'a':1.23}),
     (None, None, None, None, None, None),
     ('1', '-1', 'True', 'None', 'abc', '{\'a\': 1.23}')),
    ({'datatype': 'str'},
     (1, -1, True, None, 'abc', {'a':1.23}),
     (1, -1, True, None, 'abc', {'a':1.23}),
     (None, None, None, None, None, None),
     ('1', '-1', 'True', 'None', 'abc', '{\'a\': 1.23}')),
    ({'datatype': 'int'},
     (1, -1, True, None, 'abc', {'a':1.23}, ' 123 ', 1.99),
     (1, -1, 1, TypeError, ValueError, TypeError, 123, 1),
     (None, None, None, ValueError, ValueError, ValueError, ValueError, ValueError),
     ('1', '-1', '1', TypeError, ValueError, TypeError, '123', '1')),
    ({'datatype': 'int', 'minimum':-10, 'maximum':10},
     (1, -1, -10, 10, -11, 11, False, -7.99),
     (1, -1, -10, 10, -11, 11, 0, -7),
     (None, None, None, None, ValueError, ValueError, None, ValueError),
     ('1', '-1', '-10', '10', '-11', '11', '0', '-7')),
    ({'datatype': 'float'},
     (1.0, -1, True, None, 'abc', {'a':1.23}, ' 123 ', 1.99),
     (1.0, -1.0, 1.0, TypeError, ValueError, TypeError, 123.0, 1.99),
     (None, ValueError, ValueError, ValueError, ValueError, ValueError, ValueError, None),
     ('1.0', '-1.0', '1.0', TypeError, ValueError, TypeError, '123.0', '1.99')),
    ({'datatype': 'float', 'minimum':-10, 'maximum':10},
     (1.0, -1, -10.0, 10, -11.0, 11, False, -7.99),
     (1.0, -1.0, -10.0, 10.0, -11.0, 11.0, 0.0, -7.99),
     (None, ValueError, None, ValueError, ValueError, ValueError, ValueError, None),
     ('1.0', '-1.0', '-10.0', '10.0', '-11.0', '11.0', '0.0', '-7.99')),
])
def test_datatype_check(meta, values, cast_results, check_results, str_results):
    dt_registry = DTRegistry()

    hub = Hub(topic_factory=dt_registry)

    value = hub['value'].assign(Value(None), meta)

    assert len(values) == len(cast_results)  == len(check_results) == len(str_results)

    for value, cast_result, check_result, str_result in zip(values, cast_results, check_results, str_results):
        print('Testing', value, ', cast_result:', cast_result, ', check_result:', check_result, ', str_result:', str_result)

        try:
            if issubclass(cast_result, Exception):
                with pytest.raises(cast_result):
                    hub['value'].cast(value)
        except TypeError:
            casted_value = hub['value'].cast(value)
            assert casted_value == cast_result

        if check_result is not None:
            with pytest.raises(check_result):
                hub['value'].check(value)
        else:
            assert hub['value'].check(value) is None

        try:
            if issubclass(cast_result, Exception):
                with pytest.raises(cast_result):
                    hub['value'].checked_emit(value)
        except TypeError:
            if check_result is None:
                assert hub['value'].checked_emit(value) is None
                assert hub['value'].get() == cast_result

def test_resolve_meta_key():
    hub = Hub()

    meta = {'minimum': '>value_minimum', 'maximum':'>blabla'}
    hub['value_minimum'].assign(Value(-2))
    assert resolve_meta_key(hub, 'minimum', meta) == -2

    with pytest.raises(KeyError):
        resolve_meta_key(hub, 'maximum', meta)

def test_custom_datatype():
    dt_registry = DTRegistry()

    hub = Hub(topic_factory=dt_registry)

    class UpperCaseDT(DT):
        def cast(self, _topic, value):
            return value.upper()

        def check(self, _topic, value):
            if value != value.upper():
                raise ValueError('%r is not uppercase'%value)

    hub.topic_factory.add_datatype('uppercase', UpperCaseDT() )

    hub['value'].assign(Value(''), meta={'datatype': 'uppercase'})

    assert hub['value'].cast('This is a test') == 'THIS IS A TEST'
    assert hub['value'].check('THIS IS A TEST') is None
    with pytest.raises(ValueError):
        hub['value'].check('This is a test')

def test_validate():

    dt_registry = DTRegistry()

    hub = Hub(topic_factory=dt_registry)

    class EvenDT(DT):
        def check(self, _topic, value):
            if value%2:
                raise ValueError('%r is not even'%value)

    hub.topic_factory.add_datatype('even', EvenDT() )

    hub['value'].assign(Value(''), meta={'datatype': 'int', 'minimum':0, 'validate':'even'})

    assert hub['value'].cast('122') == 122
    assert hub['value'].check(122) is None

    with pytest.raises(ValueError):
        hub['value'].check(123)

    with pytest.raises(ValueError):
        hub['value'].check(-2)