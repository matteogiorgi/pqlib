"""Dijkstra experiments backed by the pqlib CPython extension."""

from dataclasses import dataclass, field
from math import inf
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from .path_setup import add_repo_root_to_path

add_repo_root_to_path()

import pqlib


@dataclass(order=True)
class _DijkstraEntry:
    distance: float
    sequence: int
    node: Any = field(compare=False)


def iter_neighbors(
    graph: Any,
    node: Any,
) -> Iterable[Tuple[Any, float]]:
    """Return outgoing arcs for dict-like or object-backed graphs."""

    neighbors = getattr(graph, "neighbors", None)
    if neighbors is not None:
        return neighbors(node)

    return graph.get(node, ())


def dijkstra_with_trace(
    graph: Any,
    source: Any,
    *,
    implementation: str = "binary_heap",
    node_rank_predictor: Optional[Callable[[Any, float], Optional[int]]] = None,
    key_rank_predictor: Optional[Callable[[Any, float], Optional[int]]] = None,
) -> Dict[str, Any]:
    """Run lazy Dijkstra with pqlib and collect prediction-oriented traces."""

    queue = pqlib.PriorityQueue(implementation=implementation)
    distances: Dict[Any, float] = {source: 0.0}
    finalized = set()
    extraction_order: List[Any] = []
    inserted_keys: List[float] = []
    push_trace: List[Dict[str, Any]] = []
    sequence = 0
    pop_count = 0
    stale_pop_count = 0

    def push(node: Any, distance: float, predecessor: Optional[Any]) -> None:
        nonlocal sequence

        predicted_node_rank = None
        if node_rank_predictor is not None:
            predicted_node_rank = node_rank_predictor(node, distance)

        predicted_key_rank = None
        if key_rank_predictor is not None:
            predicted_key_rank = key_rank_predictor(node, distance)

        queue.push(_DijkstraEntry(distance, sequence, node))
        inserted_keys.append(distance)
        push_trace.append({
            "sequence": sequence,
            "node": node,
            "distance": distance,
            "predecessor": predecessor,
            "predicted_node_rank": predicted_node_rank,
            "predicted_key_rank": predicted_key_rank,
            "extracted": False,
            "stale": False,
            "extraction_rank": None,
        })
        sequence += 1

    push(source, 0.0, None)

    while queue:
        entry = queue.pop()
        pop_count += 1
        event = push_trace[entry.sequence]
        if entry.node in finalized:
            stale_pop_count += 1
            event["stale"] = True
            continue
        if entry.distance != distances.get(entry.node, inf):
            stale_pop_count += 1
            event["stale"] = True
            continue

        finalized.add(entry.node)
        extraction_order.append(entry.node)
        event["extracted"] = True
        event["extraction_rank"] = len(extraction_order)

        for neighbor, weight in iter_neighbors(graph, entry.node):
            if weight < 0:
                raise ValueError("Dijkstra requires non-negative edge weights")
            if neighbor in finalized:
                continue

            candidate = entry.distance + weight
            if candidate < distances.get(neighbor, inf):
                distances[neighbor] = candidate
                push(neighbor, candidate, entry.node)

    return {
        "distances": distances,
        "extraction_order": extraction_order,
        "inserted_keys": inserted_keys,
        "push_trace": push_trace,
        "stats": {
            "pushes": len(push_trace),
            "pops": pop_count,
            "stale_pops": stale_pop_count,
            "extractions": len(extraction_order),
            "reached_nodes": len(distances),
        },
    }
