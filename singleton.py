
import threading
from functools import wraps


def singleton(thread_safe=False):
    __instances = {}
    __lock = threading.Lock() if thread_safe is True else None

    def decorator(cls):
        def get_instance(*args, **kwargs):
            if cls not in __instances:
                __instances[cls] = cls(*args, **kwargs)
            return __instances[cls]

        def thread_safe_get_instance(*args, **kwargs):
            with __lock:
                return get_instance(*args, **kwargs)

        return thread_safe_get_instance if thread_safe is True else get_instance

    if thread_safe in [True, False]:
        return decorator

    return decorator(thread_safe)

@singleton(True)
class DerivedSingleton():
    def __init__(self, filename: str, agresive=True):
        self.filename = filename
        self.agresive = agresive

obj1 = DerivedSingleton("test1.txt", agresive=False)
print(obj1.filename, obj1.agresive)

obj2 = DerivedSingleton("test2.txt", agresive=True)
print(obj2.filename, obj2.agresive)

print(obj1 is obj2)  # True


