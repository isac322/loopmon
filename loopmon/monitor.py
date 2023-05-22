from __future__ import annotations

import asyncio
import sys
from abc import ABCMeta, abstractmethod
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Optional, Tuple

from typing_extensions import Protocol, runtime_checkable


@runtime_checkable
class Callback(Protocol):
    async def __call__(self, lag: float, tasks: int, data_at: datetime) -> None:
        """
        A callback function to be called after the monitor collect metrics.
        Since all callback functions are not awaited and only create tasks,
        they do not affect the interval of the monitor.

        :param lag: The delay time of the event loop measured by the monitor.
        It is in seconds, and there may be very little error in measurement other than the actual delay time.
        :param tasks: The number of tasks currently submitted to the monitored event loop.
        :param data_at: The time the metrics were collected.
        """
        pass


class EventLoopMonitor(metaclass=ABCMeta):
    """
    It is installed in one event loop and periodically collects the loop latency and the number of running tasks.
    It is pointless to install multiple monitors in one event loop,
    and one monitor cannot be installed in multiple event loops.
    """

    _interval: float
    _callbacks: Tuple[Callback, ...]
    _name: Optional[str]
    _installed: bool

    def __init__(self, interval: float = 0.1, callbacks: Iterable[Callback] = (), name: Optional[str] = None) -> None:
        """
        It is installed in one event loop and periodically collects the loop latency and the number of running tasks.
        It is pointless to install multiple monitors in one event loop,
        and one monitor cannot be installed in multiple event loops.

        Collected metrics can be post-processed through `callbacks`, and `callbacks` do not affect the monitoring cycle
        because they are registered in the event loop rather than directly executed inside the monitor.

        If you set `interval` to a value that is too small, you won't get a meaningful value.

        There is no guarantee that the monitor will run "exactly" at intervals of `interval`.
        This is because the event loop itself is based on cooperative scheduling.

        :param interval: How often the event loop collects metrics. (seconds)
        :param callbacks: Callback functions to process metrics collected by the monitor.
        :param name: The Task name to use when installing the monitor into the event loop. [Python 3.8+ required]
        """
        super().__init__()

        self._interval = interval
        self._callbacks = tuple(callbacks)
        self._name = name
        self._installed = False

    @property
    @abstractmethod
    def running(self) -> bool:
        """
        A value indicating whether the monitor is installed in the event loop and is collecting values.
        """
        raise NotImplementedError

    @property
    def installed(self) -> bool:
        """
        A value indicating whether this monitor is already installed in a particular event loop.
        Since it runs after the monitor is installed, it can be `running == False` but `installed == True`.
        """
        return self._installed

    @property
    def interval(self) -> float:
        """
        How often the monitor collects metrics.
        """
        return self._interval

    @property
    def name(self) -> Optional[str]:
        """
        The Task name to use when installing the monitor into the event loop.
        Only supported on Python 3.8+.
        """
        return self._name

    @abstractmethod
    async def start(self) -> None:
        """
        A coroutine function to start monitoring.
        Since it is an infinite loop, it is generally not recommended to `await'.
        In general, it is recommended to use `install_to_loop`.

        If you want to run a monitor in the currently running event loop without `install_to_loop`,
        just add `asyncio.create_task(monitor.start())`.

        It must not be used in conjunction with `install_to_loop`, and either one must be used only once.
        """
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        """
        Stop the currently running monitor. If you stop a monitor that is already stopped, nothing happens.
        """
        raise NotImplementedError

    def install_to_loop(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """
        Installs the current monitor object into given event loop and runs the monitor.
        This function just commands the installation and returns immediately.
        If `loop` is not specified, get the currently running event loop.

        An error raises when an attempt is made to install in an event loop that is already closed,
        there is no event loop running, or when a monitor that is already installed is installed in the loop.

        :param loop: The event loop to install this monitor object into.
        If not specified, the currently running event loop is automatically selected.
        """

        loop = asyncio.get_running_loop() if loop is None else loop

        if loop.is_closed():
            raise ValueError('You can not monitor closed or not running loop')

        if self.installed:
            raise ValueError('This monitor already installed into (the given or other) loop')

        if sys.version_info >= (3, 8, 0):
            loop.create_task(self.start(), name=self._name)
        else:
            loop.create_task(self.start())
        self._installed = True


class SleepEventLoopMonitor(EventLoopMonitor):
    """
    Invokes `asyncio.sleep` for the specified period,
    and calculates the delay time using the time difference between before and after the invocation.
    When collection is complete, it is called by filling in the values in `callbacks` of the constructor.
    """

    _started: bool

    def __init__(self, interval: float = 0.1, callbacks: Iterable[Callback] = (), name: Optional[str] = None) -> None:
        super().__init__(interval, callbacks, name)

        self._started = False

    @property
    def running(self) -> bool:
        return self._started

    async def start(self) -> None:
        if self.running:
            raise ValueError('This monitor already installed into (the given or other) loop')

        try:
            await self._start()
        except asyncio.CancelledError:
            await self.stop()

    async def _start(self) -> None:
        self._started = True
        loop = asyncio.get_running_loop()

        while self.running:
            before = await asyncio.sleep(self.interval, result=loop.time())
            lag = loop.time() - before - self.interval
            tasks = len(asyncio.all_tasks(loop))
            data_at = datetime.now(timezone.utc)
            for c in self._callbacks:
                loop.create_task(c(lag, tasks, data_at))

    async def stop(self) -> None:
        self._installed = self._started = False
