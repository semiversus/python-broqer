from broqer.stream import Stream
import asyncio

value=Stream()

async def main():
    print('Value:', await value.as_future() )
    print(value._subscriptions)

loop=asyncio.get_event_loop()

loop.call_later(1, value.emit, 5)

loop.run_until_complete(main())