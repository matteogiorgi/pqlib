#!/usr/bin/env python3
"""Run Dijkstra prediction experiments on a DIMACS road network."""

import argparse
import csv
import json
import pathlib
import sys
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS_DIR = REPO_ROOT / "tests"
sys.path.insert(0, str(TESTS_DIR))

from learning_augmented_priority_queue import (  # noqa: E402
    aggregate_rank_stats,
    build_key_rank_predictor,
    build_node_rank_predictor,
    dijkstra_with_trace,
    key_rank_error_stats,
    load_dimacs_graph,
    node_rank_error_stats,
)


def parse_sources(raw_sources: str) -> List[int]:
    return [int(source) for source in raw_sources.split(",") if source]


def format_stats(stats: Dict[str, Any]) -> str:
    return (
        f"count={stats['count']} "
        f"avg={stats['average_error']} "
        f"max={stats['max_error']} "
        f"total={stats['total_error']}"
    )


def write_summary_json(path: pathlib.Path, summary: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_push_trace_csv(path: pathlib.Path, rows: Iterable[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run",
        "source",
        "sequence",
        "node",
        "distance",
        "predecessor",
        "predicted_node_rank",
        "predicted_key_rank",
        "extracted",
        "stale",
        "extraction_rank",
    ]
    with path.open("w", encoding="utf-8", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def run_experiment(
    graph_path: pathlib.Path,
    sources: Iterable[int],
    *,
    implementation: str,
    max_arcs: Optional[int],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    source_list = list(sources)
    load_started = time.perf_counter()
    loaded = load_dimacs_graph(graph_path, max_arcs=max_arcs)
    load_elapsed = time.perf_counter() - load_started

    print(
        "loaded",
        graph_path,
        f"nodes={loaded.node_count}",
        f"arcs={loaded.arc_count}",
        f"loaded_arcs={loaded.loaded_arc_count}",
        f"seconds={load_elapsed:.3f}",
    )

    previous_trace = None
    node_stats = []
    key_stats = []
    total_pushes = 0
    total_pops = 0
    total_stale = 0
    total_reached = 0
    run_summaries: List[Dict[str, Any]] = []
    push_rows: List[Dict[str, Any]] = []

    for index, source in enumerate(source_list, start=1):
        node_predictor = None
        key_predictor = None
        if previous_trace is not None:
            node_predictor = build_node_rank_predictor(
                previous_trace["extraction_order"]
            )
            key_predictor = build_key_rank_predictor(
                previous_trace["inserted_keys"]
            )

        started = time.perf_counter()
        trace = dijkstra_with_trace(
            loaded,
            source,
            implementation=implementation,
            node_rank_predictor=node_predictor,
            key_rank_predictor=key_predictor,
        )
        elapsed = time.perf_counter() - started
        stats = trace["stats"]
        total_pushes += stats["pushes"]
        total_pops += stats["pops"]
        total_stale += stats["stale_pops"]
        total_reached += stats["reached_nodes"]

        print(
            f"run={index}",
            f"source={source}",
            f"seconds={elapsed:.3f}",
            f"reached={stats['reached_nodes']}",
            f"pushes={stats['pushes']}",
            f"pops={stats['pops']}",
            f"stale={stats['stale_pops']}",
        )

        if previous_trace is not None:
            current_node_stats = node_rank_error_stats(trace)
            current_key_stats = key_rank_error_stats(trace["push_trace"])
            node_stats.append(current_node_stats)
            key_stats.append(current_key_stats)
            print("  node-rank", format_stats(current_node_stats))
            print("  key-rank ", format_stats(current_key_stats))
        else:
            current_node_stats = None
            current_key_stats = None
            print("  baseline run: no previous trace predictions")

        run_summaries.append({
            "run": index,
            "source": source,
            "seconds": elapsed,
            "stats": stats,
            "node_rank_error": current_node_stats,
            "key_rank_error": current_key_stats,
        })
        for event in trace["push_trace"]:
            push_rows.append({
                "run": index,
                "source": source,
                "sequence": event["sequence"],
                "node": event["node"],
                "distance": event["distance"],
                "predecessor": event["predecessor"],
                "predicted_node_rank": event["predicted_node_rank"],
                "predicted_key_rank": event["predicted_key_rank"],
                "extracted": event["extracted"],
                "stale": event["stale"],
                "extraction_rank": event["extraction_rank"],
            })

        previous_trace = trace

    print("aggregate")
    print(
        "  dijkstra",
        f"pushes={total_pushes}",
        f"pops={total_pops}",
        f"stale={total_stale}",
        f"reached_sum={total_reached}",
    )
    aggregate_node_stats = aggregate_rank_stats(node_stats)
    aggregate_key_stats = aggregate_rank_stats(key_stats)
    if node_stats:
        print("  node-rank", format_stats(aggregate_node_stats))
    if key_stats:
        print("  key-rank ", format_stats(aggregate_key_stats))

    summary = {
        "graph": {
            "path": str(graph_path),
            "node_count": loaded.node_count,
            "arc_count": loaded.arc_count,
            "loaded_arc_count": loaded.loaded_arc_count,
            "load_seconds": load_elapsed,
        },
        "configuration": {
            "sources": source_list,
            "implementation": implementation,
            "max_arcs": max_arcs,
        },
        "runs": run_summaries,
        "aggregate": {
            "dijkstra": {
                "pushes": total_pushes,
                "pops": total_pops,
                "stale_pops": total_stale,
                "reached_nodes_sum": total_reached,
            },
            "node_rank_error": aggregate_node_stats,
            "key_rank_error": aggregate_key_stats,
        },
    }
    return summary, push_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "graph",
        nargs="?",
        default=str(REPO_ROOT / "graphs" / "dimacs" / "USA-road-d.NY.gr"),
        help="DIMACS .gr graph path",
    )
    parser.add_argument(
        "--sources",
        default="1,1000,10000",
        help="comma-separated source node ids",
    )
    parser.add_argument(
        "--implementation",
        default="binary_heap",
        choices=["binary_heap", "randomized_skiplist"],
        help="pqlib backend",
    )
    parser.add_argument(
        "--max-arcs",
        type=int,
        default=None,
        help="load only the first N arcs, useful for quick smoke runs",
    )
    parser.add_argument(
        "--summary-json",
        type=pathlib.Path,
        default=None,
        help="write aggregate experiment summary as JSON",
    )
    parser.add_argument(
        "--push-trace-csv",
        type=pathlib.Path,
        default=None,
        help="write per-push trace rows as CSV",
    )
    args = parser.parse_args()

    summary, push_rows = run_experiment(
        pathlib.Path(args.graph),
        parse_sources(args.sources),
        implementation=args.implementation,
        max_arcs=args.max_arcs,
    )
    if args.summary_json is not None:
        write_summary_json(args.summary_json, summary)
        print("wrote", args.summary_json)
    if args.push_trace_csv is not None:
        write_push_trace_csv(args.push_trace_csv, push_rows)
        print("wrote", args.push_trace_csv)


if __name__ == "__main__":
    main()
