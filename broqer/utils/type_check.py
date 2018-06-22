class Type:
    name = 'none'

    def __init__(self, hub):
        self._hub = hub

    def cast(self, value, meta):
        return value

    def check(self, value, meta):
        pass

    def as_str(self, value, meta):
        return str(value)

    def _get(self, key, meta):
        if key not in meta:
            return None
        value = meta[key]
        if isinstance(value, str) and value[0] == '>':
            topic = value[1:]
            if topic not in self._hub:
                raise KeyError('topic %s not found in hub' % topic)
            return self._hub[topic].state
        return value


class IntType(Type):
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


class TypeCheck:
    default_type_classes = (Type, IntType)

    def __init__(self, hub):
        self._types = dict()
        self._hub = hub
        for type_cls in TypeCheck.default_type_classes:
            self.add_type(type_cls(hub))

    def add_type(self, type_obj: 'Type'):
        self._types[type_obj.name] = type_obj

    def cast(self, value, topic):
        '''Will cast value to the given type. It will not check the value.'''
        type_key = topic.meta.get('type', 'none')
        return self._types[type_key].cast(value, topic.meta)

    def check(self, value, topic):
        '''Check the value againt the type and limits defined in meta dictionary.
        The value has to be in the appropriate type (may use cast before)'''
        type_key = topic.meta.get('type', 'none')
        return self._types[type_key].check(value, topic.meta)


if __name__ == '__main__':
    from broqer import Hub, Value

    hub = Hub()
    type_check = TypeCheck(hub)

    value_int_meta = {'type': 'integer', 'minimum': '>value_untyped'}
    value_int = hub.assign('value_int', Value(0), meta=value_int_meta)
    value_untyped = hub.assign('value_untyped', Value(0))

    # check value_int
    assert type_check.cast('123', hub['value_int']) == 123
    assert type_check.cast(123.45, value_int) == 123
    assert type_check.cast(b'123', value_int) == 123

    assert type_check.check(123, value_int) is None
    try:
        type_check.check(-100, value_int)
    except ValueError:
        pass
    else:
        assert False, 'should raise AssertionError'

    # check value_untyped
    assert type_check.cast('123', value_untyped) == '123'
    assert type_check.cast(123.45, value_untyped) == 123.45
    assert type_check.cast(b'123', value_untyped) == b'123'

    assert type_check.check(123, value_untyped) is None
    assert type_check.check(-100, value_untyped) is None
