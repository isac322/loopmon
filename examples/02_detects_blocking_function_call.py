import asyncio
import time
from datetime import datetime

import loopmon


async def print_collected_data(lag: float, tasks: int, data_at: datetime) -> None:
    print(f'event loop lag: {lag:.3f}, running tasks: {tasks}, at {data_at}')


def blocking_function() -> None:
    # simulate blocking call in async context.
    time.sleep(1)


async def main() -> None:
    mon = loopmon.create(interval=0.1, callbacks=[print_collected_data])
    # Simple I/O bound coroutine does not occur event loop lag
    await asyncio.sleep(0.2)

    blocking_function()
    await asyncio.sleep(0.1)

    await mon.stop()


if __name__ == '__main__':
    asyncio.run(main())

# Expected output
# event loop lag: 0.000, running tasks: 2, at 2022-02-24 13:18:41.307769+00:00
# event loop lag: 1.001, running tasks: 2, at 2022-02-24 13:18:42.409116+00:00
# event loop lag: 0.000, running tasks: 1, at 2022-02-24 13:18:42.509328+00:00
