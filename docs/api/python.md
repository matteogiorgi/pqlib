# Python API

The CPython extension module is named `hpqlib`.

```python
import hpqlib
```

## class hpqlib.PriorityQueue

```python
queue = hpqlib.PriorityQueue(implementation="binary_heap")
```

`PriorityQueue` wraps one native `struct priority_queue` instance. Python
objects are stored as queue items and ordered using their natural Python
ordering.

### Constructor

```python
hpqlib.PriorityQueue(implementation="binary_heap")
```

Parameters:

- `implementation`: optional backend selector string.

Selectors:

| Selector | Status |
| --- | --- |
| `"binary_heap"` | implemented |
| `"fibonacci_heap"` | implemented |
| `"kaplan_heap"` | implemented |

Raises:

- `ValueError` if the selector is unknown;
- `MemoryError` if the native queue cannot be allocated.

### Ordering

Items inserted into the same queue must be mutually comparable with Python's
`<` and `>` operators.

With normal Python values such as integers, lower values are popped first.

If a Python comparison raises internally, the native comparator clears the
exception and treats the objects as equivalent for that comparison. Prefer
storing mutually comparable objects to avoid ambiguous ordering.

### push

```python
queue.push(item)
```

Inserts `item`.

Returns:

- `None` on success.

Raises:

- `MemoryError` if insertion fails in the native backend.

Reference behavior:

- the queue stores a strong reference to `item`;
- the reference is released when the item is popped or when the queue is
  destroyed.

### peek

```python
item = queue.peek()
```

Returns the highest-priority item without removing it.

Returns:

- the highest-priority item;
- `None` if the queue is empty.

### pop

```python
item = queue.pop()
```

Removes and returns the highest-priority item.

Returns:

- the removed item;
- `None` if the queue is empty.

Reference behavior:

- the stored strong reference is transferred back to Python as the return value.

### size

```python
count = queue.size()
```

Returns the number of stored items as an integer.

### empty

```python
is_empty = queue.empty()
```

Returns `True` when the queue contains no items.

### Protocols

`PriorityQueue` supports:

```python
len(queue)
bool(queue)
```

`len(queue)` returns the queue size. `bool(queue)` is `False` only when the
queue is empty.

## Example

```python
import hpqlib

queue = hpqlib.PriorityQueue(implementation="binary_heap")

queue.push(5)
queue.push(1)
queue.push(3)

assert queue.peek() == 1
assert queue.pop() == 1
assert len(queue) == 2
assert bool(queue)
```
