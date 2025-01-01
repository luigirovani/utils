from typing import Any
from abc import ABC
import threading

from oop.decorators import ensure
from oop.classes import SingletonThread

from functools import wraps

from typing import Callable, Dict, Set



def dynamic_inherit(*base_classes):
    """
    Decorator to dynamically inherit from one or more base classes, recursively applying inheritance.

    :param base_classes: Base classes to inherit from.
    """
    def wrapper(cls):
        new_class = cls

        for base in base_classes:
            new_class = type(new_class.__name__, (base, new_class), dict(new_class.__dict__))

        return new_class

    return wrapper





class Base(ABC):
    def __str__(self) -> str:
        return self.filename + ' ' + str(self.agresive)


class Test(Base, SingletonMixin):

    def __init__(self, filename: str, agresive=True) -> Any:
        self.filename = filename
        self.agresive = agresive


print(Test('test.txt', agresive=False))
print(Test('test2.txt'))
print(Test('test3.txt', agresive=True))


