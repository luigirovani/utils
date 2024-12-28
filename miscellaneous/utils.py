from typing import Any
from types import GeneratorType
from collections.abc import AsyncIterable

__all_ = ['is_list_like', 'convert_iter', 'to_list', 'check_async_iterable']

def is_list_like(obj: Any) -> bool:
    """ Returns `True` if the given object looks like a list-like objects."""
    return isinstance(obj, (list, tuple, set, dict, GeneratorType))

def convert_iter(obj: Any) -> list:
    """ Converts the given object to a list if it is not list-like."""
    return obj if is_list_like(obj) else [obj]

def to_list(obj: Any) -> list:
    """ Converts the given object to a list if it is not list-like, return [] if None"""
    return [_obj for _obj in convert_iter(obj) if _obj is not None]

def check_async_iterable(obj) -> bool:
    return  isinstance(obj, AsyncIterable)



