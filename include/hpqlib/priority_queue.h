#ifndef HPQLIB_PRIORITY_QUEUE_H
#define HPQLIB_PRIORITY_QUEUE_H

#include <stddef.h>

/*
 * Comparison function used to order elements in a priority queue.
 *
 * The function must return a negative value if lhs has higher priority than
 * rhs, zero if they are equivalent, and a positive value if lhs has lower
 * priority than rhs. The library never takes ownership of the pointed values.
 */
typedef int (*priority_queue_cmp_fn)(const void *lhs, const void *rhs);

/*
 * Concrete heap-priority-queue implementations available through the public
 * factory. Client code should select an implementation here and then use only
 * the abstract priority_queue operations below.
 */
enum priority_queue_implementation {
    PRIORITY_QUEUE_BINARY_HEAP = 1,
    PRIORITY_QUEUE_FIBONACCI_HEAP = 2,
    PRIORITY_QUEUE_KAPLAN_HEAP = 3
};

/*
 * Opaque priority-queue handle.
 *
 * Instances must be created with priority_queue_create() and released with
 * priority_queue_destroy().
 */
struct priority_queue;

/*
 * Create an empty priority queue backed by the selected implementation.
 *
 * Returns NULL if the implementation is unsupported, cmp is NULL, or memory
 * allocation fails.
 */
struct priority_queue *priority_queue_create(
    enum priority_queue_implementation implementation,
    priority_queue_cmp_fn cmp
);

/*
 * Destroy a priority queue created by priority_queue_create().
 *
 * This releases only memory owned by the queue itself. Stored items are not
 * destroyed. Passing NULL is allowed and has no effect.
 */
void priority_queue_destroy(struct priority_queue *queue);

/*
 * Insert an item into the priority queue.
 *
 * Returns 0 on success and -1 on failure. The item pointer is stored as-is and
 * remains owned by the caller.
 */
int priority_queue_push(struct priority_queue *queue, void *item);

/*
 * Return the highest-priority item without removing it.
 *
 * Returns NULL if the queue is NULL or empty.
 */
void *priority_queue_peek(const struct priority_queue *queue);

/*
 * Remove and return the highest-priority item.
 *
 * Returns NULL if the queue is NULL or empty. Ownership of the returned item
 * remains with the caller.
 */
void *priority_queue_pop(struct priority_queue *queue);

/*
 * Return the number of items currently stored in the queue.
 *
 * A NULL queue is treated as empty and returns 0.
 */
size_t priority_queue_size(const struct priority_queue *queue);

/*
 * Return non-zero when the queue contains no items.
 *
 * A NULL queue is treated as empty.
 */
int priority_queue_empty(const struct priority_queue *queue);

#endif
