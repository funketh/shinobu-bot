import time

import inspect
from functools import wraps, partial
from typing import Callable, TypeVar, Optional, List, Union


RT = TypeVar('RT')
P = inspect.Parameter


def configurable_decorator(decorator: Callable[..., RT]):
    sig = inspect.signature(decorator)
    params: List[P] = list(sig.parameters.values())
    try:
        specifications = (params[0].kind in [P.POSITIONAL_ONLY, P.POSITIONAL_OR_KEYWORD]
                          and all(p.default != P.empty or p.kind == P.VAR_KEYWORD for p in params[1:]))
    except IndexError:
        specifications = False
    if not specifications:
        raise ValueError('The first argument to the decorator has to be the decorated function. '
                         'Any other arguments need a default value.')

    @wraps(decorator)
    def wrapper(*args, **kwargs) -> Union[RT, Callable[..., RT]]:
        if len(args) == 1:
            if callable(args[0]):
                return decorator(args[0], **kwargs)
            raise TypeError(f'{decorator.__name__}() takes one callable positional argument')
        elif len(args) > 1:
            raise TypeError(f'{decorator.__name__}() takes one callable positional argument but {len(args)} were given')
        return partial(decorator, **kwargs)

    return wrapper


@configurable_decorator
def lazy_property(get_value: Callable[..., RT],
                  expiration_duration: Optional[int] = None) -> RT:
    attr_name = '_lazy_' + get_value.__name__

    # Redundancy for the sake of performance
    if expiration_duration is None:
        @property
        def _lazy_property(self) -> RT:
            if not hasattr(self, attr_name):
                setattr(self, attr_name, get_value(self))
            return getattr(self, attr_name)
    else:
        last_used_name = attr_name + '_last_used'

        @property
        def _lazy_property(self) -> RT:
            expired = getattr(self, last_used_name, 0) + expiration_duration \
                      >= time.time()
            if not hasattr(self, attr_name) or expired:
                setattr(self, attr_name, get_value(self))
                setattr(self, last_used_name, time.time())
            return getattr(self, attr_name)

    return _lazy_property
