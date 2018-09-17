import asyncio

from broqer import op
from broqer.subject import Subject

value = Subject()


async def main():
    print('Value: ', await (value | op.OnEmitFuture()))
    print('Value: ', await value)
    print('Number of subscribers: %d' % len(value.subscriptions))

loop = asyncio.get_event_loop()

loop.call_later(0.2, value.emit, 1)
loop.call_later(0.4, value.emit, 2)

loop.run_until_complete(main())
