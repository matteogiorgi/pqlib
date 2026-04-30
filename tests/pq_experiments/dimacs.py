"""DIMACS shortest-path graph parser for Python experiments."""

from array import array
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union


Node = int
Weight = int


@dataclass
class CsrGraph:
    """Compressed sparse row graph loaded from a DIMACS `.gr` file.

    Nodes keep their DIMACS one-based ids.  For node ``u``, outgoing arcs occupy
    ``offsets[u]`` through ``offsets[u + 1]``.
    """

    offsets: array
    heads: array
    weights: array
    node_count: int
    arc_count: int
    loaded_arc_count: int

    def neighbors(self, node: Node) -> Iterator[Tuple[Node, Weight]]:
        if node < 1 or node > self.node_count:
            return

        start = self.offsets[node]
        end = self.offsets[node + 1]
        for index in range(start, end):
            yield self.heads[index], self.weights[index]


DimacsGraph = CsrGraph


def load_dimacs_graph(
    path: Union[str, Path],
    *,
    max_arcs: Optional[int] = None,
) -> CsrGraph:
    """Load a DIMACS shortest-path graph into CSR arrays.

    Supported lines are:

    - ``c ...`` comments;
    - ``p sp <nodes> <arcs>`` problem metadata;
    - ``a <tail> <head> <weight>`` directed weighted arcs.

    ``max_arcs`` is useful for small smoke tests against large road-network
    files without loading the whole graph.
    """

    node_count: Optional[int] = None
    arc_count: Optional[int] = None
    arcs: List[Tuple[Node, Node, Weight]] = []

    with Path(path).open("r", encoding="ascii") as graph_file:
        for line_number, line in enumerate(graph_file, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("c"):
                continue

            parts = stripped.split()
            tag = parts[0]
            if tag == "p":
                if len(parts) != 4 or parts[1] != "sp":
                    raise ValueError(
                        f"unsupported DIMACS problem line at {line_number}: "
                        f"{stripped!r}"
                    )
                node_count = int(parts[2])
                arc_count = int(parts[3])
                continue

            if tag == "a":
                if len(parts) != 4:
                    raise ValueError(
                        f"invalid DIMACS arc line at {line_number}: "
                        f"{stripped!r}"
                    )
                if max_arcs is not None and len(arcs) >= max_arcs:
                    break

                tail = int(parts[1])
                head = int(parts[2])
                weight = int(parts[3])
                if weight < 0:
                    raise ValueError(
                        f"negative arc weight at line {line_number}: {weight}"
                    )
                arcs.append((tail, head, weight))
                continue

            raise ValueError(
                f"unsupported DIMACS line tag at {line_number}: {tag!r}"
            )

    if node_count is None or arc_count is None:
        raise ValueError("missing DIMACS 'p sp <nodes> <arcs>' problem line")

    return _build_csr_graph(node_count, arc_count, arcs)


def _build_csr_graph(
    node_count: int,
    arc_count: int,
    arcs: List[Tuple[Node, Node, Weight]],
) -> CsrGraph:
    degrees = array("Q", [0]) * (node_count + 2)
    for tail, head, _weight in arcs:
        if tail < 1 or tail > node_count:
            raise ValueError(f"tail node out of range: {tail}")
        if head < 1 or head > node_count:
            raise ValueError(f"head node out of range: {head}")
        degrees[tail] += 1

    offsets = array("Q", [0]) * (node_count + 2)
    running_total = 0
    for node in range(1, node_count + 1):
        offsets[node] = running_total
        running_total += degrees[node]
    offsets[node_count + 1] = running_total

    heads = array("I", [0]) * len(arcs)
    weights = array("I", [0]) * len(arcs)
    positions = array("Q", offsets)

    for tail, head, weight in arcs:
        index = positions[tail]
        heads[index] = head
        weights[index] = weight
        positions[tail] += 1

    return CsrGraph(
        offsets=offsets,
        heads=heads,
        weights=weights,
        node_count=node_count,
        arc_count=arc_count,
        loaded_arc_count=len(arcs),
    )
