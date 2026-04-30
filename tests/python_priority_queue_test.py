import pathlib
import sys

# Allow direct execution from the source tree after an in-place extension build.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

import hpqlib


def check_priority_queue(implementation):
    queue = hpqlib.PriorityQueue(implementation=implementation)

    assert not queue
    assert len(queue) == 0
    assert queue.empty()
    assert queue.peek() is None
    assert queue.pop() is None

    for value in [7, 3, 9, 1, 4, 8, 2]:
        queue.push(value)

    assert queue
    assert len(queue) == 7
    assert queue.size() == 7
    assert queue.peek() == 1
    assert [queue.pop() for _ in range(7)] == [1, 2, 3, 4, 7, 8, 9]
    assert queue.pop() is None


def test_invalid_implementation():
    try:
        hpqlib.PriorityQueue(implementation="missing")
    except ValueError:
        return

    raise AssertionError("invalid implementation was accepted")


def main():
    check_priority_queue("binary_heap")
    check_priority_queue("fibonacci_heap")
    check_priority_queue("kaplan_heap")
    test_invalid_implementation()
    print("All Python priority_queue tests passed")


if __name__ == "__main__":
    main()
