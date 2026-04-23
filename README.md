# pqlib

pqlib is a C99 library for experimenting with generic priority queues.

The project aims to expose a common abstract priority-queue API while allowing
multiple concrete implementations to coexist behind the same logical interface.
The planned implementations include binary heaps, Fibonacci heaps, Kaplan heaps
(revisited Fibonacci heaps), randomized skiplists, deterministic skiplists,
chunked skiplists, and other data structures useful for performance
comparisons.

The design follows an object-oriented style adapted idiomatically to C:
interfaces and implementations are kept separate, and concrete priority queues
can be selected at creation time while client code uses the shared API.




## Architecture

pqlib has one public abstract data type:

- `priority_queue`

The implementation families are only organizational categories:

- `heaps/`
- `skiplists/`

Concrete implementations provide the `priority_queue` behavior directly:

- `binary_heap`
- `fibonacci_heap`
- `kaplan_heap`
- `randomized_skiplist`
- `deterministic_skiplist`
- `chunked_skiplist`

There is a single public abstract API, `priority_queue`. The `heaps/` and
`skiplists/` families are not intermediate runtime abstractions, and concrete
implementations are expected to provide the `priority_queue` vtable directly.
Intermediate vtables for heaps or skiplists may be introduced later only if a
clear need emerges.




## Priority Queue Operations

The initial priority-queue interface is expected to provide:

- `create`
- `destroy`
- `push`
- `peek`
- `pop`
- `size`
- `empty`

More advanced operations may be added later:

- `decrease_key`
- `remove`
- `contains`




## Current Repository Contents

- `binaryheap.h`: public interface for the current binary-heap implementation
- `binaryheap.c`: generic min-heap implementation based on `void **` and a
  comparator function
- `binaryheap_demo.c`: usage demo program
- `binaryheap_test.c`: automated tests using `assert`
- `Makefile`: builds the object file, demo, and tests

The current code still exposes the binary heap directly. The next architectural
step is to introduce the abstract `priority_queue` API and adapt the binary
heap as its first concrete implementation.




## Useful Commands

- `make`: builds `binaryheap.o`
- `make run`: builds and runs the demo
- `make test`: builds and runs the tests
- `make clean`: removes build artifacts
