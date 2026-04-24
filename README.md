# pqlib

pqlib is a C99 library for experimenting with generic priority queues behind a
single abstract API. The library is designed so that multiple concrete data
structures can be selected at creation time while client code keeps using the
same public operations.

The repository currently contains:

- a public C API based on the opaque `struct priority_queue` type;
- a binary min-heap implementation;
- a randomized skiplist implementation;
- a CPython extension module exposing the same queue concept as
  `pqlib.PriorityQueue`.

Planned implementations include Fibonacci heaps, Kaplan heaps, deterministic
skiplists, chunked skiplists, and other structures useful for comparisons.




## Design Goals

pqlib is built around a few explicit constraints:

- The C library is written in C99 for portability.
- There is one public abstract priority-queue API.
- Concrete implementations provide the behavior directly through an internal
  vtable.
- Implementation families such as `heaps/` and `skiplists/` are organizational
  categories, not runtime abstractions.
- Stored items are generic pointers in C and remain owned by the caller.
- The Python binding stores regular Python objects and manages their reference
  counts while they are inside the queue.




## Architecture

The public C type is opaque:

```c
struct priority_queue;
```

Client code creates a queue with:

```c
struct priority_queue *priority_queue_create(
    enum priority_queue_implementation implementation,
    priority_queue_cmp_fn cmp
);
```

The selected backend embeds the common base object as its first field and
provides a private `priority_queue_vtable`. Public functions validate simple
edge cases, such as `NULL` queue handles, and dispatch to the selected backend.

Available implementations are:

| C enum | Python name | Status |
| --- | --- | --- |
| `PRIORITY_QUEUE_BINARY_HEAP` | `"binary_heap"` | implemented |
| `PRIORITY_QUEUE_RANDOMIZED_SKIPLIST` | `"randomized_skiplist"` | implemented |
| `PRIORITY_QUEUE_FIBONACCI_HEAP` | `"fibonacci_heap"` | planned |
| `PRIORITY_QUEUE_KAPLAN_HEAP` | `"kaplan_heap"` | planned |
| `PRIORITY_QUEUE_DETERMINISTIC_SKIPLIST` | `"deterministic_skiplist"` | planned |
| `PRIORITY_QUEUE_CHUNKED_SKIPLIST` | `"chunked_skiplist"` | planned |




## C API

Include the public header:

```c
#include "pqlib/priority_queue.h"
```

The comparator defines item priority:

```c
typedef int (*priority_queue_cmp_fn)(const void *lhs, const void *rhs);
```

It must return:

- a negative value if `lhs` has higher priority than `rhs`;
- zero if both items have equivalent priority;
- a positive value if `lhs` has lower priority than `rhs`.

With the current implementations, this means lower values are popped first when
the comparator follows normal ascending order.

Available operations:

```c
struct priority_queue *priority_queue_create(
    enum priority_queue_implementation implementation,
    priority_queue_cmp_fn cmp
);
void priority_queue_destroy(struct priority_queue *queue);
int priority_queue_push(struct priority_queue *queue, void *item);
void *priority_queue_peek(const struct priority_queue *queue);
void *priority_queue_pop(struct priority_queue *queue);
size_t priority_queue_size(const struct priority_queue *queue);
int priority_queue_empty(const struct priority_queue *queue);
```

`priority_queue_destroy()` releases only memory owned by the queue. It does not
free the stored items. `priority_queue_push()` stores the item pointer as-is, so
the caller must ensure that pointed objects remain valid while they are stored.




## C Example

```c
#include <stdio.h>

#include "pqlib/priority_queue.h"

static int int_cmp(const void *lhs, const void *rhs)
{
    const int *left = lhs;
    const int *right = rhs;

    if (*left < *right)
        return -1;
    if (*left > *right)
        return 1;
    return 0;
}

int main(void)
{
    int values[] = { 7, 3, 9, 1 };
    struct priority_queue *queue;
    size_t i;

    queue = priority_queue_create(PRIORITY_QUEUE_BINARY_HEAP, int_cmp);
    if (queue == NULL)
        return 1;

    for (i = 0; i < sizeof(values) / sizeof(values[0]); i++)
        priority_queue_push(queue, &values[i]);

    while (!priority_queue_empty(queue)) {
        int *value = priority_queue_pop(queue);
        printf("%d\n", *value);
    }

    priority_queue_destroy(queue);
    return 0;
}
```




## Python Bindings

pqlib also provides a CPython extension module named `pqlib`. It exposes one
class, `PriorityQueue`, which mirrors the C design by selecting the concrete
implementation at construction time.

Build and install from the repository root:

```sh
python3 -m pip install .
```

On Debian, Ubuntu, and other systems that protect the system Python
environment, install pqlib inside a virtual environment. The virtual environment
does not need to live inside the repository; you can create it anywhere and
install pqlib from the repository path:

```sh
cd /tmp
python3 -m venv pqlib-env
source pqlib-env/bin/activate
python3 -m pip install /home/matteo/doc/pqlib
```

After that, `pqlib` is importable from any directory while that virtual
environment is active.

For local development, install in editable mode:

```sh
python3 -m pip install -e .
```

You can also build the extension in-place without installing it:

```sh
make python-build
```

Python usage:

```python
import pqlib

queue = pqlib.PriorityQueue(implementation="binary_heap")
queue.push(3)
queue.push(1)
queue.push(2)

print(queue.peek())  # 1
print(queue.pop())   # 1
print(len(queue))    # 2
print(bool(queue))   # True
```

The randomized skiplist backend is selected with:

```python
queue = pqlib.PriorityQueue(implementation="randomized_skiplist")
```

Python objects are ordered with their natural Python ordering. The binding keeps
a strong reference to every object while it is stored in the queue. `pop()`
transfers that reference back to Python, and destroying a queue releases any
objects still stored in it.

Current Python methods and protocol support:

- `queue.push(item)`
- `queue.peek()`
- `queue.pop()`
- `queue.size()`
- `queue.empty()`
- `len(queue)`
- `bool(queue)`

`peek()` and `pop()` return `None` when the queue is empty.




## Build And Test

Build the C static library:

```sh
make
```

Run the C demo:

```sh
make run
```

Run the C tests:

```sh
make test
```

Build and run the Python binding smoke tests:

```sh
make python-test
```

Clean generated artifacts:

```sh
make clean
```

A direct Python test run is also possible after an in-place build:

```sh
make python-build
python3 tests/python_priority_queue_test.py
```




## Python Build Requirements

Building the Python extension requires:

- a C compiler;
- Python development headers;
- `pip`, `setuptools`, and `wheel`.

On Debian or Ubuntu, the system packages are typically:

```sh
sudo apt install build-essential python3-dev
```

Precompiled wheels are not generated yet. Until release automation is added,
`pip install .` builds the extension locally.




## Repository Layout

- `include/`: public headers installed or consumed by client code.
- `include/pqlib/priority_queue.h`: public priority-queue API.
- `src/`: private C implementation sources.
- `src/priority_queue.c`: public API dispatch and implementation factory.
- `src/priority_queue_internal.h`: internal base object layout and vtable.
- `src/heaps/`: heap-based implementations.
- `src/heaps/binary_heap.c`: binary min-heap backend.
- `src/skiplists/`: skiplist-based implementations.
- `src/skiplists/randomized_skiplist.c`: randomized skiplist backend.
- `python/`: CPython extension source.
- `python/pqlibmodule.c`: Python binding implementation.
- `examples/`: small C usage examples.
- `tests/`: C and Python tests.
- `legacy/`: original binary-heap implementation kept as reference code.
- `Makefile`: C build, demo, tests, and Python helper targets.
- `pyproject.toml`, `setup.py`, `MANIFEST.in`: Python packaging files.
- `ISTRUZIONI.txt`: project notes and architectural requirements.




## Current Limitations

The initial public API intentionally stays small:

- `create`
- `destroy`
- `push`
- `peek`
- `pop`
- `size`
- `empty`

Future operations may include:

- `decrease_key`
- `remove`
- `contains`

The Python binding currently supports natural Python ordering only. Custom
`key=` or `cmp=` callables are not implemented yet.
