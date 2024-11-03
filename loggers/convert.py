import logging


def convert_level(level):
    if isinstance(level, str):
        return getattr(logging, level.upper().replace('ING', ''), logging.NOTSET)
        
    return level



