from broqer import op, Value


# build_sink

@op.build_sink
def info(msg):
    print('Info:', msg)


v = Value('Busy')
v.subscribe(info)


# build_sink_factory

@op.build_sink_factory
def warning(postfix, msg):
    print('Warning:', msg, postfix)


v = Value('Godzilla!')
doomed_sink = warning('You are doomed!')
v.subscribe(doomed_sink)


# sink_property

class Test:
    @op.sink_property
    def alarm(self, msg):
        print('Alarm!', msg)

    @op.sink_property(unpack=True)
    def add(self, a, b):
        """ The add susbscriber """
        print(f'{a} + {b} = {a+b}')


t = Test()

v2 = Value()
v2.subscribe(t.alarm)
v2.emit('Fire!')

v3 = Value((1, 2))
v3.subscribe(t.add)
