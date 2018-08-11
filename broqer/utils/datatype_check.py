from broqer.hub import MetaTopic

class DT:
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


class IntDT(DT):
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


class DTCheck:
    default_datatype_classes = (Datatype, IntDatatype)

    def __init__(self, hub_):
        self._datatypes = dict()
        self._hub = hub_
        for datatype_cls in DatatypeCheck.default_datatype_classes:
            self.add_datatype(datatype_cls(hub_))

    def add_datatype(self, datatype_obj: 'Datatype'):
        self._datatypes[datatype_obj.name] = datatype_obj



class DTTopic(MetaTopic):
    def __init__(self, hub: 'Hub', path: str) -> None:
        MetaTopic.__init__(self, hub, path)
        self._hub = hub

    def cast(self, value):
        '''Will cast value to the given datatype. It will not check the
        value.
        '''
        return self._hub.topic_factory.cast(hub, value, self._meta)

    def check(self, value):
        '''Check the value against the datatype and limits defined in meta
        dictionary. The value has to be in the appropriate datatype (may use
        cast before)
        '''
        self._hub.topic_factory.check(hub, value, self._meta)

    def checked_emit(self, value: Any) -> asyncio.Future:
        value = self.cast(value)
        self.check(value)
        return self._subject.emit(value, who=self)

class DTRegistry:
    default_datatype_classes = (Datatype, IntDatatype)

    def __init__(self):
        self._datatypes = dict()
        for datatype_cls in self.default_datatype_classes:
            self.add_datatype(datatype_cls)

    def add_datatype(self, name: str, dt: DT):
        self._datatypes

    def __call__(self, hub: 'Hub', path: str) -> None:
        return DTTopic(hub, path, self)

    def cast(self, hub, value, meta):
