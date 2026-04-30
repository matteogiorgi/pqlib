"""Rank-prediction priority-queue prototype for Python experiments."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Union

from .path_setup import add_repo_root_to_path

add_repo_root_to_path()

import pqlib


@dataclass(order=True)
class _RankEntry:
    priority: Any
    sequence: int
    item: Any = field(compare=False)


class RankPredictionPriorityQueue:
    """Rank-prediction prototype built on the native pqlib queue.

    The paper's rank-prediction model gives every inserted key a prediction of
    its final rank among all keys. This first Python prototype records those
    prediction errors while preserving exact priority-queue semantics through
    the native pqlib queue.
    """

    def __init__(
        self,
        *,
        key: Optional[Callable[[Any], Any]] = None,
        implementation: str = "binary_heap",
    ) -> None:
        self._key = key if key is not None else (lambda item: item)
        self._queue = pqlib.PriorityQueue(implementation=implementation)
        self._sequence = 0
        self._size = 0
        self._insertions = 0
        self._rank_error_total = 0
        self._rank_error_count = 0
        self._max_rank_error = 0

    def push(
        self,
        item: Any,
        *,
        priority: Any = None,
        predicted_rank: int,
        true_rank: Optional[int] = None,
    ) -> None:
        """Insert an item with a predicted final rank."""

        true_priority = self._key(item) if priority is None else priority
        self._queue.push(_RankEntry(true_priority, self._sequence, item))
        self._sequence += 1
        self._size += 1
        self._insertions += 1

        if true_rank is not None:
            self._record_rank_error(true_rank, predicted_rank)

    def peek(self) -> Any:
        entry = self._queue.peek()
        if entry is None:
            return None
        return entry.item

    def pop(self) -> Any:
        entry = self._queue.pop()
        if entry is None:
            return None

        self._size -= 1
        return entry.item

    def empty(self) -> bool:
        return self._size == 0

    def size(self) -> int:
        return self._size

    def stats(self) -> Dict[str, Union[float, int, None]]:
        average_error = None
        if self._rank_error_count:
            average_error = self._rank_error_total / self._rank_error_count

        return {
            "size": self._size,
            "insertions": self._insertions,
            "rank_prediction_error_count": self._rank_error_count,
            "max_rank_prediction_error": self._max_rank_error,
            "average_rank_prediction_error": average_error,
        }

    def __len__(self) -> int:
        return self._size

    def __bool__(self) -> bool:
        return not self.empty()

    def _record_rank_error(self, true_rank: int, predicted_rank: int) -> None:
        error = abs(true_rank - predicted_rank)
        self._rank_error_total += error
        self._rank_error_count += 1
        self._max_rank_error = max(self._max_rank_error, error)
