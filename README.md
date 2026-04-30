# hpqlib

hpqlib is a C99 library for experimenting with heap-priority-queues behind a
single abstract API. The library is intentionally focused on heap-based
implementations so comparisons stay compact and specialized.

The repository currently contains:

- a public C API based on the opaque `struct priority_queue` type;
- binary min-heap, Fibonacci heap, and Kaplan heap implementations;
- a CPython extension module exposing the same queue concept as
  `hpqlib.PriorityQueue`;
- additional documentation under `docs/`.

Implemented heap-based backends include binary heaps, Fibonacci heaps, and
Kaplan heaps.




## Design Goals

hpqlib is built around a few explicit constraints:

- The C library is written in C99 for portability.
- There is one public abstract priority-queue API.
- Concrete implementations provide the behavior directly through an internal
  vtable.
- `heaps/` is the implementation family for concrete backends.
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
| `PRIORITY_QUEUE_FIBONACCI_HEAP` | `"fibonacci_heap"` | implemented |
| `PRIORITY_QUEUE_KAPLAN_HEAP` | `"kaplan_heap"` | implemented |




## C Example

```c
#include <stdio.h>

#include "hpqlib/priority_queue.h"

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

hpqlib also provides a CPython extension module named `hpqlib`. It exposes one
class, `PriorityQueue`, which mirrors the C design by selecting the concrete
implementation at construction time.

Build and install from the repository root:

```sh
python3 -m pip install .
```

This source installation compiles the extension during installation. It does not
require running `make python-build` first, but it does require a C compiler and
Python development headers on the machine performing the install.

On Debian, Ubuntu, and other systems that protect the system Python
environment, install hpqlib inside a virtual environment. The virtual environment
does not need to live inside the repository; you can create it anywhere and
install hpqlib from the repository path:

```sh
cd /tmp
python3 -m venv hpqlib-env
source hpqlib-env/bin/activate
python3 -m pip install /home/matteo/doc/hpqlib
```

After that, `hpqlib` is importable from any directory while that virtual
environment is active.

For local development, install in editable mode:

```sh
python3 -m pip install -e .
```

You can also build the extension in-place without installing it:

```sh
make python-build
```

To install from a prebuilt wheel instead of compiling locally:

```sh
python3 -m pip install dist/hpqlib-*.whl
```

Python usage:

```python
import hpqlib

queue = hpqlib.PriorityQueue(implementation="binary_heap")
queue.push(3)
queue.push(1)
queue.push(2)

print(queue.peek())  # 1
print(queue.pop())   # 1
print(len(queue))    # 2
print(bool(queue))   # True
```

The `"kaplan_heap"` selector exposes the simple Fibonacci heap described in
`docs/papers/fibonacci_heaps_revisited.pdf`.

## Build And Test

Build the C static library:

```sh
make
```

Run the C tests:

```sh
make test
```

Build and run the Python binding smoke tests:

```sh
make python-test
```

Build a wheel for the current platform and Python version:

```sh
make wheel
```

Run the local release workflow:

```sh
make release VERSION=0.1.0
```

Build and upload the wheel to a GitHub Release:

```sh
make release-upload VERSION=0.1.0
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
`pip install .` builds the extension locally. The project includes a basic
`cibuildwheel` configuration in `pyproject.toml` for future release automation
across multiple Python versions and operating systems.




## Repository Layout

- `include/`: public headers installed or consumed by client code.
- `include/hpqlib/priority_queue.h`: public priority-queue API.
- `src/`: private C implementation sources.
- `src/priority_queue.c`: public API dispatch and implementation factory.
- `src/priority_queue_internal.h`: internal base object layout and vtable.
- `src/heaps/`: heap-based implementations.
- `src/heaps/binary_heap.c`: binary min-heap backend.
- `src/heaps/fibonacci_heap.c`: Fibonacci heap backend.
- `src/heaps/kaplan_heap.c`: Kaplan heap backend.
- `python/`: CPython extension source.
- `python/hpqlibmodule.c`: Python binding implementation.
- `docs/`: focused documentation pages for C usage, Python usage, and
  packaging.
- `release.sh`: internal release helper used by the Makefile release targets.
- `tests/`: C and Python tests.
- `results/`: optional generated outputs kept outside the test tree.
- `Makefile`: C build, demo, tests, and Python helper targets.
- `pyproject.toml`, `setup.py`, `MANIFEST.in`: Python packaging files.
- `ISTRUZIONI.md`: project notes and architectural requirements.




## Additional Documentation

The README is the main entry point. More focused documentation is available in:

- [docs/index.md](docs/index.md)
- [docs/api/priority_queue.md](docs/api/priority_queue.md)
- [docs/api/implementations.md](docs/api/implementations.md)
- [docs/api/python.md](docs/api/python.md)
- [docs/building.md](docs/building.md)




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
