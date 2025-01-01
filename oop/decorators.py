import threading

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

def ensure(method):
    def wrapper(self, *args, **kwargs):
        attribute_name = f"_{method.__name__}"
        if not hasattr(self, attribute_name):
            setattr(self, attribute_name, None)
        return method(self, *args, **kwargs)
    
    return wrapper





