from collections.abc import Callable
from typing import TypeVar
import time

T = TypeVar("T")


def retry(operation: Callable[[], T], attempts: int = 3, delay_s: float = 0.2) -> T:
    last_exc: Exception | None = None
    for idx in range(attempts):
        try:
            return operation()
        except Exception as exc:  # pragma: no cover - branch validated in caller tests
            last_exc = exc
            if idx < attempts - 1:
                time.sleep(delay_s)
    assert last_exc is not None
    raise last_exc
