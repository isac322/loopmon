import asyncio
from datetime import datetime

import loopmon


async def print_collected_data(lag: float, tasks: int, data_at: datetime) -> None:
    print(f'event loop lag: {lag:.3f}, running tasks: {tasks}, at {data_at}')


idx = 0


async def some_long_waited_coroutine(_: float, __: int, ___: datetime) -> None:
    global idx
    print(f'[{idx:02d}] before long wait')
    idx += 1
    await asyncio.sleep(2)
    print(f'[{idx:02d}] after long wait')


async def main() -> None:
    loopmon.create(interval=1, callbacks=[print_collected_data, some_long_waited_coroutine])
    await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())

# Expected output: monitor never wait to callbacks finish.
#
# event loop lag: 0.001, running tasks: 2, at 2022-02-24 12:05:18.875319+00:00
# [00] before long wait
# event loop lag: 0.001, running tasks: 3, at 2022-02-24 12:05:19.876509+00:00
# [01] before long wait
# [02] after long wait
# event loop lag: 0.000, running tasks: 3, at 2022-02-24 12:05:20.876712+00:00
# [02] before long wait
# [03] after long wait
# event loop lag: 0.000, running tasks: 3, at 2022-02-24 12:05:21.876951+00:00
# [03] before long wait
