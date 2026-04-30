"""Prediction and error-measure helpers for Python experiments."""

from bisect import bisect_right
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, TypeVar, Union


T = TypeVar("T")


def true_ranks(
    items: Iterable[T],
    *,
    key: Optional[Callable[[T], Any]] = None,
) -> Dict[T, int]:
    """Return one-based true ranks for a distinct-key test fixture."""

    key_fn = key if key is not None else (lambda item: item)
    item_list = list(items)
    sorted_items = sorted(item_list, key=key_fn)

    if len({key_fn(item) for item in sorted_items}) != len(sorted_items):
        raise ValueError("rank prediction fixtures must use distinct keys")

    return {item: rank for rank, item in enumerate(sorted_items, start=1)}


def rank_prediction_stats(
    rank_pairs: Iterable[Tuple[int, int]]
) -> Dict[str, Union[float, int, None]]:
    """Summarize absolute errors between true and predicted ranks."""

    errors = [
        abs(true_rank - predicted_rank)
        for true_rank, predicted_rank in rank_pairs
    ]
    if not errors:
        return {
            "count": 0,
            "total_error": 0,
            "max_error": None,
            "average_error": None,
        }

    total_error = sum(errors)
    return {
        "count": len(errors),
        "total_error": total_error,
        "max_error": max(errors),
        "average_error": total_error / len(errors),
    }


def build_node_rank_predictor(
    extraction_order: Iterable[Any],
    *,
    default_rank: Optional[int] = None,
) -> Callable[[Any, float], Optional[int]]:
    """Build a predictor from nodes to their previous extraction rank."""

    ranks = {node: rank for rank, node in enumerate(extraction_order, start=1)}

    def predict(node: Any, _distance: float) -> Optional[int]:
        return ranks.get(node, default_rank)

    return predict


def build_key_rank_predictor(
    inserted_keys: Iterable[float],
) -> Callable[[Any, float], int]:
    """Predict a key rank by locating it among keys from a previous run."""

    sorted_keys = sorted(inserted_keys)

    def predict(_node: Any, distance: float) -> int:
        return bisect_right(sorted_keys, distance) + 1

    return predict


def key_rank_error_stats(push_trace: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Compare predicted key ranks against ranks within one Dijkstra run."""

    events = list(push_trace)
    sorted_events = sorted(
        events,
        key=lambda event: (event["distance"], event["sequence"]),
    )
    true_ranks_by_sequence = {
        event["sequence"]: rank
        for rank, event in enumerate(sorted_events, start=1)
    }
    rank_pairs = [
        (true_ranks_by_sequence[event["sequence"]], event["predicted_key_rank"])
        for event in events
        if event["predicted_key_rank"] is not None
    ]

    return rank_prediction_stats(rank_pairs)


def node_rank_error_stats(trace: Dict[str, Any]) -> Dict[str, Any]:
    """Compare predicted node ranks against final extraction ranks."""

    true_node_ranks = {
        node: rank
        for rank, node in enumerate(trace["extraction_order"], start=1)
    }
    rank_pairs = [
        (true_node_ranks[event["node"]], event["predicted_node_rank"])
        for event in trace["push_trace"]
        if event["predicted_node_rank"] is not None
        and event["node"] in true_node_ranks
    ]

    return rank_prediction_stats(rank_pairs)


def aggregate_rank_stats(
    stats_list: Iterable[Dict[str, Union[float, int, None]]]
) -> Dict[str, Union[float, int, None]]:
    """Aggregate rank-error stats returned by this module."""

    stats = list(stats_list)
    total_count = sum(int(item["count"]) for item in stats)
    total_error = sum(int(item["total_error"]) for item in stats)
    max_values: List[int] = [
        int(item["max_error"])
        for item in stats
        if item["max_error"] is not None
    ]

    average_error = None
    if total_count:
        average_error = total_error / total_count

    return {
        "count": total_count,
        "total_error": total_error,
        "max_error": max(max_values) if max_values else None,
        "average_error": average_error,
    }
