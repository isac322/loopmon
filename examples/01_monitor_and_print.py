import asyncio
from datetime import datetime

import loopmon


async def print_collected_data(lag: float, tasks: int, data_at: datetime) -> None:
    print(f'event loop lag: {lag:.3f}, running tasks: {tasks}, at {data_at}')


async def main() -> None:
    loopmon.create(interval=0.5, callbacks=[print_collected_data])
    await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(main())

# Expected output
# event loop lag: 0.001, running tasks: 2, at 2022-02-23 15:29:40.766393+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-23 15:29:41.267072+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-23 15:29:41.767736+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-23 15:29:42.268396+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-23 15:29:42.769055+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-23 15:29:43.269690+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-23 15:29:43.770309+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-23 15:29:44.270959+00:00
# event loop lag: 0.001, running tasks: 2, at 2022-02-23 15:29:44.771620+00:00
