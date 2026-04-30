# Heap Implementations

hpqlib is intentionally limited to heap-priority-queue implementations. All
backends are selected through `priority_queue_create()` and then used through
the same public `priority_queue` API.

## Summary

| Backend | C selector | Python selector | Status |
| --- | --- | --- | --- |
| Binary heap | `PRIORITY_QUEUE_BINARY_HEAP` | `"binary_heap"` | implemented |
| Fibonacci heap | `PRIORITY_QUEUE_FIBONACCI_HEAP` | `"fibonacci_heap"` | implemented |
| Kaplan heap | `PRIORITY_QUEUE_KAPLAN_HEAP` | `"kaplan_heap"` | implemented |

## binary_heap

Status: implemented.

Source files:

- `src/heaps/binary_heap.c`
- `src/heaps/binary_heap.h`

Data structure:

- contiguous binary min-heap array;
- comparator-driven ordering;
- caller-owned item pointers.

Expected operation costs:

| Operation | Cost |
| --- | --- |
| `priority_queue_push` | `O(log n)` |
| `priority_queue_peek` | `O(1)` |
| `priority_queue_pop` | `O(log n)` |
| `priority_queue_size` | `O(1)` |
| `priority_queue_empty` | `O(1)` |

Notes:

- equal-priority items are not guaranteed to pop in insertion order;
- allocation grows the backing array as needed.

## fibonacci_heap

Status: implemented.

Source files:

- `src/heaps/fibonacci_heap.c`
- `src/heaps/fibonacci_heap.h`

Data structure:

- circular doubly linked root list;
- circular doubly linked child lists;
- minimum-node pointer;
- delete-min consolidation by root degree.

Expected operation costs:

| Operation | Cost |
| --- | --- |
| `priority_queue_push` | amortized `O(1)` |
| `priority_queue_peek` | `O(1)` |
| `priority_queue_pop` | amortized `O(log n)` |
| `priority_queue_size` | `O(1)` |
| `priority_queue_empty` | `O(1)` |

Notes:

- the current public API does not expose `decrease_key`;
- the node layout keeps parent/child/degree/mark fields so the backend can be
  extended later;
- equal-priority items are not guaranteed to pop in insertion order.

## kaplan_heap

Status: implemented.

Source files:

- `src/heaps/kaplan_heap.c`
- `src/heaps/kaplan_heap.h`

This backend implements the simple Fibonacci heap from "Fibonacci Heaps
Revisited", referred to in this project as a Kaplan heap.

Data structure:

- one heap-ordered tree per queue;
- doubly linked child lists;
- rank per node;
- delete-min consolidation through fair links, followed by naive links.

Expected operation costs:

| Operation | Cost |
| --- | --- |
| `priority_queue_push` | amortized `O(1)` |
| `priority_queue_peek` | `O(1)` |
| `priority_queue_pop` | amortized `O(log n)` |
| `priority_queue_size` | `O(1)` |
| `priority_queue_empty` | `O(1)` |

Notes:

- the current public API does not expose `decrease_key`;
- the node layout keeps parent/child/rank/mark fields so the backend can be
  extended later;
- equal-priority items are not guaranteed to pop in insertion order.
