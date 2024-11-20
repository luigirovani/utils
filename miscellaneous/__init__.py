import os
import sys
import platform
import asyncio
import random
import warnings
from typing import Any
from types import GeneratorType
from collections.abc import AsyncIterable, Coroutine, Iterable, Callable, Awaitable


DELAY = float (os.getenv('DELAY', 1))
DELAY_FACTOR = int(os.getenv('DELAY_FACTOR', 10))

async def sleep(delay: float|int = DELAY, factor: int = DELAY_FACTOR) -> None:
    await asyncio.sleep(random.uniform(
        delay/factor, 
        delay*2
    ))

def is_list_like(obj: Any) -> bool:
    """ Returns `True` if the given object looks like a list-like objects."""
    return isinstance(obj, (list, tuple, set, dict, GeneratorType))

def convert_iter(obj: Any) -> list:
    """ Converts the given object to a list if it is not list-like."""
    return obj if is_list_like(obj) else [obj]

async def check_async_iterable(obj) -> bool:
    return  isinstance(obj, AsyncIterable)

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

def os_is_windows() -> bool:
    return platform.system() == 'Windows'

def os_is_linux() -> bool:
    return platform.system() == 'Linux'

def set_loop() -> None:
    if os_is_linux():
        try:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        except ImportError:
            warnings.warn('Use uvloop for better performance')

def get_loop() -> asyncio.AbstractEventLoop:
    if os_is_linux():
        try:
            import uvloop
            return uvloop
        except ImportError:
            warnings.warn('Use uvloop for better performance')
    return asyncio

class StdoutFilter:
    def __init__(self, std_out = sys.stdout, blacklist=[], whitelist=[], case_sensitive=False):
        self.std_out = std_out
        self.case_sensitive = case_sensitive
        self.blacklist = list(blacklist) if not case_sensitive else [word.lower() for word in blacklist]
        self.whitelist = list(whitelist) if not case_sensitive else [word.lower() for word in whitelist]
        
    def write(self, text):
        if self.filter(text):
            self.std_out.write(text)

    def flush(self):
        self.std_out.flush()

    def filter(self, text):
        words = text if self.case_sensitive else text.lower()

        if any(word in words for word in self.blacklist):
            return False

        if self.whitelist and not any(word in words for word in self.whitelist):
            return False

        return True





