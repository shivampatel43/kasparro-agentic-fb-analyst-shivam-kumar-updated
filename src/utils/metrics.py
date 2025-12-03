import time
from contextlib import contextmanager
from typing import Dict, Iterator


@contextmanager
def timed(metrics: Dict[str, float], key: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        end = time.perf_counter()
        metrics[key] = (end - start) * 1000.0  # ms
