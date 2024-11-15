import logging
from typing import Union


def convert_level(level: Union[str, int]) -> int:
    if isinstance(level, str):
        return getattr(logging, level.upper().replace('ING', ''), logging.DEBUG)
        
    return level



