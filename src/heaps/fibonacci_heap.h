#ifndef HPQLIB_HEAPS_FIBONACCI_HEAP_H
#define HPQLIB_HEAPS_FIBONACCI_HEAP_H

#include "hpqlib/priority_queue.h"

/*
 * Create a priority_queue backed by a Fibonacci heap.
 *
 * This is a private factory used by the public priority_queue_create()
 * dispatcher. The returned object must be handled only through the abstract
 * priority_queue API.
 */
struct priority_queue *fibonacci_heap_create(priority_queue_cmp_fn cmp);

#endif
