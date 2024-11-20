import os
import sys
import platform
import asyncio
import random
import warnings

from typing import Union

DELAY = float (os.getenv('DELAY', 1))
DELAY_FACTOR = int(os.getenv('DELAY_FACTOR', 10))

async def sleep(delay: Union[float, int] = DELAY, factor: int = DELAY_FACTOR) -> None:
    await asyncio.sleep(random.uniform(
        delay/factor, 
        delay*2 + (delay/factor*2) 
    ))

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





