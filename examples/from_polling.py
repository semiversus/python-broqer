from broqer import op
import asyncio
import subprocess

(op.FromPolling(1, subprocess.check_output, 'uptime')
 | op.map(str, encoding='utf - 8')
 | op.map(str.split, sep=', ')
 | op.pluck(0)
 | op.sink(print)
 )

loop = asyncio.get_event_loop()
loop.run_until_complete(asyncio.sleep(10))
