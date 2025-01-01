import threading
from abc import ABC, abstractclassmethod

class Singleton(type):
    __instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instances:
            cls.__instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls.__instances[cls]

class SingletonThread(Singleton):
    __lock = threading.Lock()

    def __call__(cls):
        with cls.__lock:
            return super()(cls)



