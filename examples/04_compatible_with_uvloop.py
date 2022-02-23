import asyncio
from datetime import datetime

import uvloop

import loopmon


async def print_collected_data(lag: float, tasks: int, data_at: datetime) -> None:
    print(f'event loop lag: {lag:.3f}, running tasks: {tasks}, at {data_at}')


async def main() -> None:
    loopmon.create(interval=0.5, callbacks=[print_collected_data])
    await asyncio.sleep(5)


if __name__ == '__main__':
    uvloop.install()
    asyncio.run(main())

# Expected output
# event loop lag: 0.001, running tasks: 2, at 2022-02-24 13:08:39.846741+00:00
# event loop lag: 0.000, running tasks: 2, at 2022-02-24 13:08:40.347377+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-24 13:08:40.848002+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-24 13:08:41.348621+00:00
# event loop lag: 0.000, running tasks: 2, at 2022-02-24 13:08:41.849226+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-24 13:08:42.349839+00:00
# event loop lag: 0.000, running tasks: 2, at 2022-02-24 13:08:42.850437+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-24 13:08:43.351026+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-24 13:08:43.851625+00:00
