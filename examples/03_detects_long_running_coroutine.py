import asyncio
from datetime import datetime

import loopmon


async def print_collected_data(lag: float, tasks: int, data_at: datetime) -> None:
    print(f'event loop lag: {lag:.3f}, running tasks: {tasks}, at {data_at}')


def cpu_heavy_function() -> int:
    # CPU intensive function does not yield event loop

    def fibonacci(n: int) -> int:
        if n <= 2:
            return 1
        return fibonacci(n - 1) + fibonacci(n - 2)

    return fibonacci(35)


async def main() -> None:
    mon = loopmon.create(interval=0.1, callbacks=[print_collected_data])
    # Simple I/O bound coroutine does not occur event loop lag
    await asyncio.sleep(0.2)

    cpu_heavy_function()
    await asyncio.sleep(0.1)

    await mon.stop()


if __name__ == '__main__':
    asyncio.run(main())

# Expected output
# event loop lag: 0.000, running tasks: 2, at 2022-02-24 13:19:17.361667+00:00
# event loop lag: 0.973, running tasks: 2, at 2022-02-24 13:19:18.435124+00:00 <- lag depends on you CPU
# event loop lag: 0.000, running tasks: 1, at 2022-02-24 13:19:18.535331+00:00
