class Datatype:
    name = 'none'

    def __init__(self, hub_):
        self._hub = hub_

    def cast(self, value, meta):  # pylint: disable=unused-argument,no-self-use
        return value

    def check(self, value,
              meta):  # pylint: disable=unused-argument,no-self-use
        pass

    def as_str(self, value,
               meta):  # pylint: disable=unused-argument,no-self-use
        return str(value)

    def _get(self, key, meta):
        if key not in meta:
            return None
        value = meta[key]
        if isinstance(value, str) and value[0] == '>':
            topic = value[1:]
            if topic not in self._hub:
                raise KeyError('topic %s not found in hub' % topic)
            return self._hub[topic].get()
        return value


class IntDatatype(Datatype):
    name = 'integer'

    def cast(self, value, meta):
        return int(value)

    def check(self, value, meta):
        minimum = self._get('minimum', meta)
        if minimum is not None and value < minimum:
            raise ValueError('Value %d under minimum of %d' % (value, minimum))

        maximum = self._get('maximum', meta)
        if maximum is not None and value > maximum:
            raise ValueError('Value %d over maximum of %d' % (value, maximum))


class DatatypeCheck:
    default_datatype_classes = (Datatype, IntDatatype)

    def __init__(self, hub_):
        self._datatypes = dict()
        self._hub = hub_
        for datatype_cls in DatatypeCheck.default_datatype_classes:
            self.add_datatype(datatype_cls(hub))

    def add_datatype(self, datatype_obj: 'Datatype'):
        self._datatypes[datatype_obj.name] = datatype_obj

    def cast(self, value, topic):
        '''Will cast value to the given datatype. It will not check the
        value.
        '''
        datatype_key = topic.meta.get('datatype', 'none')
        return self._datatypes[datatype_key].cast(value, topic.meta)

    def check(self, value, topic):
        '''Check the value againt the datatype and limits defined in meta
        dictionary. The value has to be in the appropriate datatype (may use
        cast before)
        '''
        datatype_key = topic.meta.get('datatype', 'none')
        return self._datatypes[datatype_key].check(value, topic.meta)


if __name__ == '__main__':
    from broqer import Hub, Value

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
    try:
        datatype_check.check(-100, value_int)
    except ValueError:
        pass
    else:
        assert False, 'should raise AssertionError'

    # check value_untyped
    assert datatype_check.cast('123', value_untyped) == '123'
    assert datatype_check.cast(123.45, value_untyped) == 123.45
    assert datatype_check.cast(b'123', value_untyped) == b'123'

    assert datatype_check.check(123, value_untyped) is None
    assert datatype_check.check(-100, value_untyped) is None
