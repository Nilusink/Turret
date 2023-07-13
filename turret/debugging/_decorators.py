from traceback import format_exc
import typing as tp


_P = tp.ParamSpec("_P")
_R = tp.TypeVar("_R")


def print_traceback(callback: tp.Callable[[str], None]):
    def decorator(func: tp.Callable[[_P], _R]):
        def wrapper(*args: _P, **kwargs: _P) -> _R:
            try:
                return func(*args, **kwargs)

            except Exception:
                callback(
                    f"Exception occurred in {func.__name__!r}:\n{format_exc()}"
                )
                raise

        return wrapper
    return decorator
