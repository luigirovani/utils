def singleton(cls):
    instances = {}  

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance  

def ensure(method):
    def wrapper(self, *args, **kwargs):
        attribute_name = f"_{method.__name__}"
        if not hasattr(self, attribute_name):
            setattr(self, attribute_name, None)
        return method(self, *args, **kwargs)
    
    return wrapper




