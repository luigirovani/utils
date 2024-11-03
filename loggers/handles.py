import sys
import logging
from logging.handlers import BaseRotatingHandler, TimedRotatingFileHandler
from logging import FileHandler, StreamHandler
from pathlib import Path
from typing import Union

import colorlog
from colorlog import ColoredFormatter

from ..miscellaneous import os_is_linux
from.consts import colorful, normal, COLOUR_LOG_PATTERN

try:
    from concurrent_log_handler import ConcurrentTimedRotatingFileHandler 
except ImportError:
    ConcurrentTimedRotatingFileHandler = TimedRotatingFileHandler


DATEFTM = "%d-%m-%Y %H:%M:%S"


def create_dir(path: Union[str, Path], unix_logs: bool = True) -> str:
    path_file = Path(path) if isinstance(path, str) else path
    
    if unix_logs and os_is_linux():
        dir_app = Path(sys.argv[0]).resolve().parent
        path_file = Path("/var/log") / dir_app.name / path_file
    
    path_file.parent.mkdir(parents=True, exist_ok=True)
    
    return str(path_file.absolute())


def get_colour_stdout_handler(
    fmt: str = colorful.LEVEL_TIME_MSG, 
    level: int = logging.INFO,
    datefmt: str = DATEFTM,
    reset: bool = True,
    log_colors: dict = COLOUR_LOG_PATTERN,
    **keyargs
) -> StreamHandler:

    stdout_handler = colorlog.StreamHandler()
    stdout_handler.setLevel(level)  
    stdout_formater = ColoredFormatter(fmt, datefmt, reset=reset, log_colors=log_colors, **keyargs)
    stdout_handler.setFormatter(stdout_formater)
    return stdout_handler

def get_stdout_handler(
    fmt: str = normal.LEVEL_TIME_MSG, 
    level: int = logging.INFO,
    datefmt: str = DATEFTM
) -> StreamHandler:

    stdout_handler = StreamHandler()
    stdout_handler.setLevel(level)  
    stdout_formater = logging.Formatter(fmt, datefmt)
    stdout_handler.setFormatter(stdout_formater)
    return stdout_handler

def get_file_handler(
    file: Union[Path, str] = 'logs.log', 
    level: int = logging.INFO, 
    fmt: str = normal.NAME_LEVEL_TIME_MSG,
    datefmt: str = DATEFTM,
    mode: str ='a',
    **keyargs
    ) -> FileHandler: 

    file_handler = FileHandler(file, encoding='utf-8', mode=mode, **keyargs)
    file_handler.setLevel(level)
    formater = logging.Formatter(fmt, datefmt)
    file_handler.setFormatter(formater)
    return file_handler


def get_rotative_handler(
    file: Union[Path, str], 
    level: int = logging.INFO, 
    multiprocess: bool = False,
    when: str ='midnight', 
    backupCount: int = 14,
    fmt: str = normal.NAME_LEVEL_TIME_MSG,
    datefmt: str = DATEFTM,
    **keyargs
    ) -> BaseRotatingHandler:

    Handler = ConcurrentTimedRotatingFileHandler if multiprocess else TimedRotatingFileHandler

    handler = Handler(
        create_dir(file), 
        when=when, 
        backupCount=backupCount, 
        encoding='utf-8', 
        **keyargs
    )
    handler.setLevel(level)
    formater = logging.Formatter(fmt, datefmt)
    handler.setFormatter(formater)
    return handler

def get_colour_rotative_handler(
    file: Union[Path, str], 
    level: int = logging.INFO, 
    multiprocess: bool = False,
    when: str ='midnight', 
    backupCount: int = 14,
    fmt: str = colorful.NAME_LEVEL_TIME_MSG,
    datefmt: str = DATEFTM,
    reset: bool = True,
    log_colors: dict = COLOUR_LOG_PATTERN,
    **keyargs
    ) -> BaseRotatingHandler:

    Handler = ConcurrentTimedRotatingFileHandler if multiprocess else TimedRotatingFileHandler

    handler = Handler(
        create_dir(file), 
        when=when, 
        backupCount=backupCount, 
        encoding='utf-8', 
        **keyargs
    )
    handler.setLevel(level)
    formater = ColoredFormatter(fmt, datefmt, reset=reset, log_colors=log_colors)
    handler.setFormatter(formater)
    return handler
