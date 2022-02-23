from __future__ import annotations

import asyncio
from typing import Any, Optional, Type, TypeVar, cast, overload

from loopmon.monitor import Callback, EventLoopMonitor, SleepEventLoopMonitor

_MT = TypeVar('_MT', bound=EventLoopMonitor)

__all__ = (
    'Callback',
    'EventLoopMonitor',
    'SleepEventLoopMonitor',
    'create',
)


@overload
def create(
    loop: Optional[asyncio.AbstractEventLoop] = None,
    monitor_cls: Type[SleepEventLoopMonitor] = SleepEventLoopMonitor,
    *args: Any,
    **kwargs: Any,
) -> SleepEventLoopMonitor:
    pass


@overload
def create(
    loop: Optional[asyncio.AbstractEventLoop],
    monitor_cls: Type[_MT],
    *args: Any,
    **kwargs: Any,
) -> _MT:
    pass


# https://github.com/python/mypy/issues/3737#issuecomment-465355737
def create(  # type: ignore[no-untyped-def]
    loop: Optional[asyncio.AbstractEventLoop] = None,
    monitor_cls=SleepEventLoopMonitor,
    *args: Any,
    **kwargs: Any,
) -> _MT:
    """
    Creates a monitor object that can monitor an event loop, installs it in a given event loop, and starts monitoring.
    This function just commands the installation and returns immediately. (doesn't block)

    If `monitor_cls` is not specified, `SleepEventLoopMonitor` is used,
    so parameters such as `interval` `callbacks` `name` can be specified as `kwargs`.

    Example:

    ```
    async def print_monitored_data(lag: float, tasks: int, data_at: datetime) -> None:
        print(lag, tasks, data_at)

    async def main():
        monitor = loopmon.create(interval=0.1, callbacks=[print_monitored_data])
    ```

    If `loop` is not specified, get the currently running event loop.
    If there is no event loop running, an error is raised. So you should not invoke this method on module scope.

    :param loop: The event loop to install this monitor object into.
    If not specified, the currently running event loop is automatically selected.
    :param monitor_cls: The class of the monitor. If not specified, `SleepEventLoopMonitor` is used.
    :param args: Parameters to pass to the `monitor_cls` constructor
    :param kwargs: Parameters to pass to the `monitor_cls` constructor
    :return:
    """

    mon = cast(Type[_MT], monitor_cls)(*args, **kwargs)
    mon.install_to_loop(loop)
    return mon
