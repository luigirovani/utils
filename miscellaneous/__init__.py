import os
import platform
import asyncio
import warnings

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




