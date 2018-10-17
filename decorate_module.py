from types import FunctionType
from functools import wraps
import logging as log
from inspect import getcallargs


def decorate_all_in_module(module, decorator):
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, FunctionType):
            setattr(module, name, decorator(obj))


def log_decorator(fun):
    @wraps(fun)
    def wrapper(*args, **kwargs):
        log.info(
            "Called "
            + str(fun)
            + " with args: "
            + str(getcallargs(fun, *args, **kwargs))
        )
        retval = fun(*args, **kwargs)
        log.info("Returned " + str(retval))
        return retval

    return wrapper
