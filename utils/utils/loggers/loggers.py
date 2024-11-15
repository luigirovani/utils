# -*- coding: utf-8 -*-
import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from logging import StreamHandler, FileHandler, Formatter
from datetime import datetime
from typing import Union, List, Dict, Optional, Tuple

from datetime import datetime
import os

import pytz
import colorama
colorama.init(autoreset=True)
from colorama import Fore, Back, Style

from .colourprinter import colourprinter
from .convert import convert_level
os.environ["TZ"] = 'America/Sao_Paulo'

class Converters:
    @staticmethod
    def convert_level(level):
        if isinstance(level, str):
            return getattr(logging, level.upper().replace('ING', ''), logging.NOTSET)
        
        return level
    
class TimeZoneFormatter(logging.Formatter):
    def __init__(
        self, 
        fmt='%(name)s - %(asctime)s - %(levelname)s - %(message)s', 
        datefmt="%d-%m-%Y %H:%M:%S", 
        tz='America/Sao_Paulo'
    ):
        super().__init__(fmt, datefmt)
        self.tz = pytz.timezone(tz)
        self.datefmt = datefmt

    def formatTime(self, record, datefmt=None) -> str:
        return self.converter(record.created).strftime(self.datefmt)
    
    def converter(self, timestamp) -> datetime:
        return datetime.fromtimestamp(timestamp).astimezone(self.tz)

class WordFilter(logging.Filter):
    def __init__(self, level, blacklist):
        self.level = level
        self.blacklist = list(blacklist)

    def filter(self, record):
        message = record.getMessage()
        if record.levelno == self.level:
           return not (any (word in message for word in self.blacklist))
        return True

class Logger(logging.Logger):
    def __init__(
            self, 
            name: str = __name__, 
            file: str = 'log.log', 
            file_handler = None,
            level_file: Union[int, str, None] = logging.INFO,
            level_stdout: Union[int, str, None] = None,
            formatter_file:str = '%(asctime)s - %(levelname)s - %(message)s',
            formatter_stdout:str = '%(asctime)s - %(levelname)s - %(message)s',
            timezone:str = 'America/Sao_Paulo',
            datefmt:str = "%d-%m-%Y %H:%M:%S",
            colour=False,
            blacklist:List[str] = [],
            rotative: bool = True,
            backupCount: int = 7,
            ):
        
        self._file = file
        self._level_file = convert_level(level_file)
        self._level_stdout = convert_level(level_stdout)
        super().__init__(name)

        self._timezone = pytz.timezone(timezone)
        self._file_handler = file_handler
        self._datefmt = datefmt
        self._formatter_file = formatter_file
        self._formatter_stdout = formatter_stdout
        self._colour = colour
        self._blacklist = list(blacklist)
        self._rotative = rotative
        self._backupCount = backupCount
        self._setup_logger()
 
    def _setup_logger(self):
        if self._level_stdout:
            self._setup_std()
        if self._level_file:
            self._setup_file()

    def _setup_std(self):
        handler = StreamHandler()
        handler.setLevel(self._level_stdout)
        formatter = TimeZoneFormatter(
            fmt=self._formatter_file, 
            datefmt=self._datefmt,
            tz=self._timezone
        )
        handler.setFormatter(formatter)
        if self._blacklist:
            handler.addFilter(WordFilter(self._level_file, self._blacklist))
        self.addHandler(handler)

    def _setup_file(self):
        if self._file_handler:
            handler = self._file_handler

        elif self._rotative:
            f = os.path.abspath(self._file)
            os.makedirs(os.path.dirname(f), exist_ok=True)
            handler = TimedRotatingFileHandler(
                f, 
                when='S', 
                encoding='utf-8', 
                backupCount=self._backupCount
            )

        else:
            handler = FileHandler(self._file, encoding='utf-8')

        handler.setLevel(self._level_file)
        formatter = TimeZoneFormatter(
            fmt=self._formatter_file, 
            datefmt=self._datefmt,
            tz=self._timezone
        )
        handler.setFormatter(formatter)
        if self._blacklist:
            handler.addFilter(WordFilter(self._level_file, self._blacklist))
        self.addHandler(handler)


    def get_time(self):
        return datetime.now(self._timezone).strftime(self._datefmt) + ' - '
                

    def print_output(self, msg, level=None, colour=None, stack_info=False, print_time=False):

        _level = convert_level(level)
        time = self.get_time() if print_time else ''
        text = time + msg

        if self._colour or colour:
            colourprinter(text, _level, colour)
        else:
            print(text)
        
        if _level:
            self.log(_level, msg, stack_info=stack_info)

