import functools
import time
from typing import Any, Callable, Type, Tuple


class RetryError(RuntimeError):
    """Raised when a retried operation fails permanently."""


def retry(
    *,
    max_attempts: int = 3,
    base_delay: float = 0.2,
    backoff_factor: float = 2.0,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    on_retry: Callable[[int, BaseException], None] | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Simple exponential backoff retry decorator.

    - `max_attempts`: total attempts including the first one.
    - `base_delay`: delay before the second attempt.
    - `backoff_factor`: multiplier for each subsequent delay.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 0
            delay = base_delay
            last_exc: BaseException | None = None
            while attempt < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:  # type: ignore[misc]
                    last_exc = exc
                    attempt += 1
                    if attempt >= max_attempts:
                        break
                    if on_retry is not None:
                        on_retry(attempt, exc)
                    time.sleep(delay)
                    delay *= backoff_factor
            raise RetryError(f"Function {func.__name__} failed after {max_attempts} attempts") from last_exc

        return wrapper

    return decorator
