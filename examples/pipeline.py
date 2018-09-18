import asyncio
import statistics

from broqer import op
from broqer.subject import Subject

adc_raw = Subject()

(adc_raw
 | op.Cache(0)
 | op.Map(lambda d: d * 5 + 3)
 | op.Sample(0.3)
 | op.SlidingWindow(5)
 | op.Map(statistics.mean)
 | op.Cache()
 | op.Debounce(0.5)
 | op.Sink(print)
 )


async def main():
    await asyncio.sleep(2)
    adc_raw.emit(50)
    await asyncio.sleep(2)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
