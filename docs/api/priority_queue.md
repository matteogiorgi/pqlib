# priority_queue

`priority_queue` is the public C abstract data type exposed by hpqlib. It
represents a heap-priority-queue selected at construction time and used through
one common API.

## Synopsis

```c
#include "hpqlib/priority_queue.h"
```

```c
struct priority_queue;

typedef int (*priority_queue_cmp_fn)(const void *lhs, const void *rhs);

enum priority_queue_implementation {
    PRIORITY_QUEUE_BINARY_HEAP = 1,
    PRIORITY_QUEUE_FIBONACCI_HEAP = 2,
    PRIORITY_QUEUE_KAPLAN_HEAP = 3
};
```

## Description

`struct priority_queue` is opaque. Client code creates an instance with
`priority_queue_create()` and then uses only the public functions documented
below.

Concrete backends embed a common internal base object and provide an internal
vtable. That dispatch detail is private; users should select a backend only
through `enum priority_queue_implementation`.

## Comparator Contract

```c
typedef int (*priority_queue_cmp_fn)(const void *lhs, const void *rhs);
```

The comparator defines priority order:

- return a negative value when `lhs` has higher priority than `rhs`;
- return zero when both items have equivalent priority;
- return a positive value when `lhs` has lower priority than `rhs`.

With a normal ascending comparator, smaller values are popped first.

The comparator must be valid for every pair of items stored in the same queue.
If stored objects become invalid while still inside the queue, behavior is
undefined from the caller's side of the contract.

## Ownership

The queue stores `void *` item pointers. It does not copy, free, or otherwise
own the objects those pointers refer to.

Destroying a queue releases only memory allocated by the queue implementation.
Items still stored in the queue remain caller-owned.

## Implementations

| Selector | Status |
| --- | --- |
| `PRIORITY_QUEUE_BINARY_HEAP` | implemented |
| `PRIORITY_QUEUE_FIBONACCI_HEAP` | implemented |
| `PRIORITY_QUEUE_KAPLAN_HEAP` | implemented |

See [Heap Implementations](implementations.md) for backend-specific notes.

## Functions

### priority_queue_create

```c
struct priority_queue *priority_queue_create(
    enum priority_queue_implementation implementation,
    priority_queue_cmp_fn cmp
);
```

Creates an empty queue backed by `implementation`.

Parameters:

- `implementation`: concrete heap backend selector.
- `cmp`: comparator used to order stored items.

Returns:

- a queue handle on success;
- `NULL` if `cmp` is `NULL`;
- `NULL` if `implementation` is unsupported;
- `NULL` if allocation fails.

Ownership:

- the returned queue must be released with `priority_queue_destroy()`;
- stored items remain owned by the caller.

### priority_queue_destroy

```c
void priority_queue_destroy(struct priority_queue *queue);
```

Destroys a queue created by `priority_queue_create()`.

Parameters:

- `queue`: queue handle, or `NULL`.

Behavior:

- passing `NULL` is allowed and has no effect;
- queue-owned memory is released;
- stored items are not destroyed.

### priority_queue_push

```c
int priority_queue_push(struct priority_queue *queue, void *item);
```

Inserts `item` into `queue`.

Parameters:

- `queue`: queue handle.
- `item`: caller-owned pointer to store.

Returns:

- `0` on success;
- `-1` if `queue` is `NULL`;
- `-1` if allocation fails inside the backend.

Ownership:

- the queue stores `item` as-is;
- the caller must keep the pointed object valid while it is stored.

### priority_queue_peek

```c
void *priority_queue_peek(const struct priority_queue *queue);
```

Returns the highest-priority item without removing it.

Parameters:

- `queue`: queue handle, or `NULL`.

Returns:

- the highest-priority stored item;
- `NULL` if `queue` is `NULL`;
- `NULL` if the queue is empty.

### priority_queue_pop

```c
void *priority_queue_pop(struct priority_queue *queue);
```

Removes and returns the highest-priority item.

Parameters:

- `queue`: queue handle, or `NULL`.

Returns:

- the removed item;
- `NULL` if `queue` is `NULL`;
- `NULL` if the queue is empty.

Ownership:

- ownership of the pointed item remains with the caller;
- hpqlib never frees the returned item.

### priority_queue_size

```c
size_t priority_queue_size(const struct priority_queue *queue);
```

Returns the number of items currently stored.

Parameters:

- `queue`: queue handle, or `NULL`.

Returns:

- the number of stored items;
- `0` if `queue` is `NULL`.

### priority_queue_empty

```c
int priority_queue_empty(const struct priority_queue *queue);
```

Reports whether the queue is empty.

Parameters:

- `queue`: queue handle, or `NULL`.

Returns:

- non-zero when the queue is empty;
- non-zero when `queue` is `NULL`;
- zero when the queue contains at least one item.

## Example

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
