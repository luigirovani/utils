import logging
import asyncio
import random
import os
import warnings
from typing import List, Optional, Union, Any
from collections.abc import AsyncIterable, Coroutine, Iterable, Callable, Awaitable

from .os_utils import *
from .utils import *
from .decorators import ensure

__all__ = ['sleep', 'run_async', 'Runner', 'get_loop', 'get_runner', 'set_loop']

DELAY = float (os.getenv('DELAY', 1))
DELAY_FACTOR = int(os.getenv('DELAY_FACTOR', 10))

async def sleep(delay: float|int = DELAY, factor: int = DELAY_FACTOR) -> None:
    """ Sleeps for a random time in average delay seconds if delay is not None and > 0"""
    if delay:
        await asyncio.sleep(random.uniform(
            delay/factor, 
            delay*2
        ))

async def run_async(
    iterable: Iterable | AsyncIterable, 
    func: Callable[..., Coroutine[Any, Any, Any]], 
    parallel: bool = True, 
    return_exceptions: bool = True,
    **kwargs: Any
) -> Awaitable[Any]:

    if check_async_iterable(iterable):
        async for item in iterable:
            await func(item, **kwargs)

    elif parallel:
        return await asyncio.gather(
            *[func(item, **kwargs) for item in convert_iter(iterable)], 
            return_exceptions=return_exceptions
        )

    else:
        for item in convert_iter(iterable):
            await func(item, **kwargs)


def set_loop() -> None:
    if os_is_linux():
        try:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        except ImportError:
            warnings.warn('Use uvloop for better performance')

def get_runner():
    if os_is_linux():
        try:
            import uvloop
            return uvloop
        except ImportError:
            warnings.warn('Use uvloop for better performance')
    return asyncio

def get_loop() -> asyncio.AbstractEventLoop:
    set_loop()
    return asyncio.get_event_loop()

FatalException = (SystemExit, asyncio.CancelledError, KeyboardInterrupt)

class Runner:
    def __init__(
        self, 
        coros: List[asyncio.Future]|asyncio.Future = [], 
        name: Optional[str] = __name__, 
        logger: Optional[logging.Logger] = None, 
        max_tasks: Optional[int] = None, 
        loop: Optional[asyncio.AbstractEventLoop] = None, 
        timout: Optional[float] = None, 
        return_exceptions: bool = False, 
        delay: Optional[Union[float, int]] = None
    ) -> None:
        self.name: str = name
        self._tasks: List[asyncio.Future] = []
        self._results: List[Any] = []
        self.logger: Optional[logging.Logger] = logger
        self._sem: Optional[asyncio.Semaphore] = None
        self._cancel_running = False
        self.max_tasks = max_tasks
        self.loop: asyncio.AbstractEventLoop = loop
        self.future: asyncio.Future = self.loop.create_future()
        self.timout: Optional[float] = timout
        self.delay: Optional[Union[float, int]] = delay
        self.return_exceptions: bool = return_exceptions
        for coro in to_list(coros):
            self.push(coro)

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, logger):
        if not logger:
            self._logger = logging.getLogger(self.name)
            self._logger.setLevel(logging.DEBUG)
        else:
            self._logger = logger.getChild(self.name)

    @property
    def loop(self):
        return self._loop

    @loop.setter
    @ensure
    def loop(self, loop: asyncio.AbstractEventLoop|None = None):
        if self.loop and self._tasks:
            raise RuntimeError('Cannot change loop while tasks are running')

        self._loop = loop or get_loop()

    @property
    def max_tasks(self):
        return self._sem._value if self._sem else None

    @max_tasks.setter
    def max_tasks(self, max_tasks: int):
        if not self._sem:
            self._sem = asyncio.Semaphore(max_tasks) if max_tasks else None
        elif max_tasks:
            self._sem._value = max_tasks

    @property
    def future(self):
        return self._future

    @future.setter
    @ensure
    def future(self, future: asyncio.Future| None = None):
        if self._future and not self._future.done():
            self._future.cancel()

        self._future = future or self.loop.create_future()
        self._future.add_done_callback(self.on_future_done)

    @property
    def results(self):
        results = []
        while len (self._results) > 0:
            results.append(self._results.pop(0))

        return results

    @results.setter
    def results(self, result: asyncio.Future):
        try:
            self._results.append(result.result())
        except FatalException as e:
            pass
        except Exception as e:
            self._results.append(e)

        self._tasks.remove(result)

    def push(self, coro):
        async def run_coro():
            async def _run_coro():
                await sleep(self.delay)
                try:
                    return await asyncio.wait_for(coro, self.timout)
                except asyncio.TimeoutError:
                    pass

            if self._sem:
                async with self._sem:
                    return await _run_coro()
            else:
                return await _run_coro()

        task = self.loop.create_task(run_coro())
        task.add_done_callback(self.on_task_done)
        self._tasks.append(task)
        return task

    def on_task_done(self, finished_task: asyncio.Future):
        for task in list(self._tasks):
            if task is finished_task:
                self.results = task

    def on_future_done(self, future: asyncio.Future):

        for task in list(self._tasks):
            if not task.done():
                task.cancel()

        if future.done():
            try:
                if result := future.result():
                    self.logger.info(f'Finished: {result}')
            except FatalException:
                self.logger.warning(f'Cancelled')
                pass
            except Exception as e:
                self.logger.critical(f'Error : {e}', exc_info=True)

    def __await__(self):
        return self.run().__await__()

    async def run(self):
        self._cancel_running = False
        tasks = self._tasks

        try:
            await asyncio.gather(*tasks, return_exceptions=self.return_exceptions)
            self.finish("All tasks finish")
        except (asyncio.CancelledError, KeyboardInterrupt):
            self.finish(None)
        except Exception as e:
            self.finish(e=e)

        await self.future
        return self.results

    def finish(self, result = None, e = None):
        if not self.future.done() and not self._cancel_running:
            if e:
                self.loop.call_later(0.1, self.future.set_exception, e)
            else:
                self.loop.call_later(0.1, self.future.set_result, result)
            self._cancel_running = True



