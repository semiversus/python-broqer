from broqer.stream import Stream
import asyncio

adc_raw=Stream()

voltage=adc_raw.map(lambda d:d*5+3).sample(0.3).sink(print)

async def main():
    await asyncio.sleep(0.5)
    adc_raw.emit(50)
    await asyncio.sleep(2)

loop=asyncio.get_event_loop()
loop.run_until_complete(main())