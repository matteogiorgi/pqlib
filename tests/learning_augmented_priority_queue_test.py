import pathlib
import csv
import json
import sys

# Allow direct execution from the source tree after an in-place extension build.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "experiments"))

from road_network_experiment import (  # noqa: E402
    write_push_trace_csv,
    write_summary_json,
)

from learning_augmented_priority_queue import (
    RankPredictionPriorityQueue,
    aggregate_rank_stats,
    build_key_rank_predictor,
    build_node_rank_predictor,
    dijkstra_with_trace,
    key_rank_error_stats,
    load_dimacs_graph,
    node_rank_error_stats,
    true_ranks,
)


def drain(queue):
    values = []
    while queue:
        values.append(queue.pop())
    return values


def test_true_ranks_are_one_based_and_distinct():
    ranks = true_ranks([7, 3, 9, 1])

    assert ranks == {
        1: 1,
        3: 2,
        7: 3,
        9: 4,
    }

    try:
        true_ranks([1, 1, 2])
    except ValueError:
        return

    raise AssertionError("duplicate keys were accepted in a rank fixture")


def test_rank_predictions_with_perfect_predictions():
    values = [7, 3, 9, 1, 4, 8, 2]
    ranks = true_ranks(values)
    queue = RankPredictionPriorityQueue(implementation="binary_heap")

    for value in values:
        queue.push(
            value,
            predicted_rank=ranks[value],
            true_rank=ranks[value],
        )

    assert queue.peek() == 1
    assert drain(queue) == [1, 2, 3, 4, 7, 8, 9]

    stats = queue.stats()
    assert stats["rank_prediction_error_count"] == len(values)
    assert stats["max_rank_prediction_error"] == 0
    assert stats["average_rank_prediction_error"] == 0


def test_rank_predictions_with_bounded_noise():
    values = [7, 3, 9, 1, 4, 8, 2]
    ranks = true_ranks(values)
    offsets = {
        1: 0,
        2: 1,
        3: -1,
        4: 2,
        7: -2,
        8: 1,
        9: 0,
    }
    queue = RankPredictionPriorityQueue(implementation="randomized_skiplist")

    for value in values:
        queue.push(
            value,
            predicted_rank=ranks[value] + offsets[value],
            true_rank=ranks[value],
        )

    assert drain(queue) == [1, 2, 3, 4, 7, 8, 9]

    stats = queue.stats()
    assert stats["max_rank_prediction_error"] == 2
    assert stats["average_rank_prediction_error"] == 1


def test_rank_predictions_with_reversed_predictions_still_pop_in_true_order():
    values = [7, 3, 9, 1, 4, 8, 2]
    ranks = true_ranks(values)
    n = len(values)
    queue = RankPredictionPriorityQueue(implementation="binary_heap")

    for value in values:
        queue.push(
            value,
            predicted_rank=n + 1 - ranks[value],
            true_rank=ranks[value],
        )

    assert drain(queue) == [1, 2, 3, 4, 7, 8, 9]

    stats = queue.stats()
    assert stats["max_rank_prediction_error"] == 6
    assert stats["insertions"] == len(values)


def test_rank_predictions_with_explicit_priorities():
    items = [
        ("slow", 30),
        ("fast", 5),
        ("middle", 20),
    ]
    ranks = true_ranks(items, key=lambda item: item[1])
    queue = RankPredictionPriorityQueue(
        key=lambda item: item[1],
        implementation="randomized_skiplist",
    )

    for item in items:
        queue.push(
            item,
            predicted_rank=ranks[item],
            true_rank=ranks[item],
        )

    assert [name for name, _priority in drain(queue)] == [
        "fast",
        "middle",
        "slow",
    ]


def sample_graph():
    return {
        "A": [("B", 1), ("C", 4)],
        "B": [("C", 2), ("D", 5)],
        "C": [("D", 1), ("E", 3)],
        "D": [("E", 1)],
        "E": [],
    }


def test_dijkstra_with_trace_uses_pqlib_priority_queue():
    trace = dijkstra_with_trace(
        sample_graph(),
        "A",
        implementation="binary_heap",
    )

    assert trace["distances"] == {
        "A": 0.0,
        "B": 1.0,
        "C": 3.0,
        "D": 4.0,
        "E": 5.0,
    }
    assert trace["extraction_order"] == ["A", "B", "C", "D", "E"]
    assert [event["node"] for event in trace["push_trace"]] == [
        "A",
        "B",
        "C",
        "C",
        "D",
        "D",
        "E",
        "E",
    ]
    assert trace["inserted_keys"] == [
        0.0,
        1.0,
        4.0,
        3.0,
        6.0,
        4.0,
        6.0,
        5.0,
    ]
    assert trace["stats"] == {
        "pushes": 8,
        "pops": 8,
        "stale_pops": 3,
        "extractions": 5,
        "reached_nodes": 5,
    }
    assert [
        event["sequence"]
        for event in trace["push_trace"]
        if event["extracted"]
    ] == [0, 1, 3, 5, 7]
    assert [
        event["sequence"]
        for event in trace["push_trace"]
        if event["stale"]
    ] == [2, 4, 6]


def test_dijkstra_node_rank_predictions_from_previous_run():
    graph = sample_graph()
    previous = dijkstra_with_trace(graph, "A")
    predictor = build_node_rank_predictor(previous["extraction_order"])
    current = dijkstra_with_trace(
        graph,
        "B",
        implementation="randomized_skiplist",
        node_rank_predictor=predictor,
    )

    assert current["distances"] == {
        "B": 0.0,
        "C": 2.0,
        "D": 3.0,
        "E": 4.0,
    }
    assert current["extraction_order"] == ["B", "C", "D", "E"]

    stats = node_rank_error_stats(current)
    assert stats["count"] == 6
    assert stats["max_error"] == 1
    assert stats["average_error"] == 1


def test_dijkstra_key_rank_predictions_from_previous_run():
    graph = sample_graph()
    previous = dijkstra_with_trace(graph, "A")
    predictor = build_key_rank_predictor(previous["inserted_keys"])
    current = dijkstra_with_trace(
        graph,
        "B",
        key_rank_predictor=predictor,
    )

    stats = key_rank_error_stats(current["push_trace"])
    assert stats["count"] == len(current["push_trace"])
    assert stats["max_error"] == 2
    assert stats["total_error"] == 8


def test_aggregate_rank_stats():
    aggregate = aggregate_rank_stats([
        {"count": 2, "total_error": 5, "max_error": 3, "average_error": 2.5},
        {"count": 3, "total_error": 6, "max_error": 4, "average_error": 2.0},
    ])

    assert aggregate == {
        "count": 5,
        "total_error": 11,
        "max_error": 4,
        "average_error": 2.2,
    }


def test_load_dimacs_graph(tmp_path=None):
    if tmp_path is None:
        tmp_path = pathlib.Path("/tmp")

    graph_path = tmp_path / "small-road.gr"
    graph_path.write_text(
        "\n".join([
            "c small DIMACS shortest path fixture",
            "p sp 4 5",
            "a 1 2 7",
            "a 2 3 11",
            "a 1 3 20",
            "a 3 4 5",
            "a 4 1 1",
        ]),
        encoding="ascii",
    )

    loaded = load_dimacs_graph(graph_path)

    assert loaded.node_count == 4
    assert loaded.arc_count == 5
    assert loaded.loaded_arc_count == 5
    assert list(loaded.neighbors(1)) == [(2, 7), (3, 20)]
    assert list(loaded.neighbors(2)) == [(3, 11)]
    assert list(loaded.neighbors(3)) == [(4, 5)]
    assert list(loaded.neighbors(4)) == [(1, 1)]

    trace = dijkstra_with_trace(loaded, 1)
    assert trace["distances"] == {
        1: 0.0,
        2: 7.0,
        3: 18.0,
        4: 23.0,
    }


def test_load_dimacs_graph_can_limit_large_inputs(tmp_path=None):
    if tmp_path is None:
        tmp_path = pathlib.Path("/tmp")

    graph_path = tmp_path / "partial-road.gr"
    graph_path.write_text(
        "\n".join([
            "p sp 3 3",
            "a 1 2 5",
            "a 2 3 6",
            "a 3 1 7",
        ]),
        encoding="ascii",
    )

    loaded = load_dimacs_graph(graph_path, max_arcs=2)

    assert loaded.node_count == 3
    assert loaded.arc_count == 3
    assert loaded.loaded_arc_count == 2
    assert list(loaded.neighbors(1)) == [(2, 5)]
    assert list(loaded.neighbors(2)) == [(3, 6)]
    assert list(loaded.neighbors(3)) == []


def test_road_network_experiment_writes_summary_json(tmp_path=None):
    if tmp_path is None:
        tmp_path = pathlib.Path("/tmp")

    output_path = tmp_path / "pqlib-summary.json"
    write_summary_json(output_path, {"aggregate": {"pushes": 3}})

    assert json.loads(output_path.read_text(encoding="utf-8")) == {
        "aggregate": {
            "pushes": 3,
        },
    }


def test_road_network_experiment_writes_push_trace_csv(tmp_path=None):
    if tmp_path is None:
        tmp_path = pathlib.Path("/tmp")

    output_path = tmp_path / "pqlib-push-trace.csv"
    write_push_trace_csv(output_path, [
        {
            "run": 1,
            "source": 7,
            "sequence": 0,
            "node": 7,
            "distance": 0.0,
            "predecessor": None,
            "predicted_node_rank": None,
            "predicted_key_rank": 1,
            "extracted": True,
            "stale": False,
            "extraction_rank": 1,
        }
    ])

    with output_path.open("r", encoding="utf-8", newline="") as csv_file:
        rows = list(csv.DictReader(csv_file))

    assert rows == [{
        "run": "1",
        "source": "7",
        "sequence": "0",
        "node": "7",
        "distance": "0.0",
        "predecessor": "",
        "predicted_node_rank": "",
        "predicted_key_rank": "1",
        "extracted": "True",
        "stale": "False",
        "extraction_rank": "1",
    }]


def main():
    test_true_ranks_are_one_based_and_distinct()
    test_rank_predictions_with_perfect_predictions()
    test_rank_predictions_with_bounded_noise()
    test_rank_predictions_with_reversed_predictions_still_pop_in_true_order()
    test_rank_predictions_with_explicit_priorities()
    test_dijkstra_with_trace_uses_pqlib_priority_queue()
    test_dijkstra_node_rank_predictions_from_previous_run()
    test_dijkstra_key_rank_predictions_from_previous_run()
    test_aggregate_rank_stats()
    test_load_dimacs_graph()
    test_load_dimacs_graph_can_limit_large_inputs()
    test_road_network_experiment_writes_summary_json()
    test_road_network_experiment_writes_push_trace_csv()
    print("All learning-augmented priority_queue tests passed")


if __name__ == "__main__":
    main()
