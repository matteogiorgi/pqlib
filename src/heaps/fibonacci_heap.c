#include <stdlib.h>

#include "heaps/fibonacci_heap.h"
#include "priority_queue_internal.h"

/*
 * Fibonacci-heap implementation of the abstract priority_queue API.
 *
 * This backend implements the operations currently exposed by hpqlib:
 * create/destroy/push/peek/pop/size/empty.  The decrease-key machinery from
 * the original paper is not exposed by the public API yet, but the node layout
 * keeps the usual parent/child/rank/mark fields so the backend can grow in that
 * direction later.
 */
struct fibonacci_heap_node {
    void *item;
    struct fibonacci_heap_node *parent;
    struct fibonacci_heap_node *child;
    struct fibonacci_heap_node *left;
    struct fibonacci_heap_node *right;
    size_t degree;
    int marked;
};

struct fibonacci_heap {
    struct priority_queue base;
    struct fibonacci_heap_node *minimum;
    size_t size;
};

static void fibonacci_heap_destroy(struct priority_queue *queue);
static int fibonacci_heap_push(struct priority_queue *queue, void *item);
static void *fibonacci_heap_peek(const struct priority_queue *queue);
static void *fibonacci_heap_pop(struct priority_queue *queue);
static size_t fibonacci_heap_size(const struct priority_queue *queue);
static int fibonacci_heap_empty(const struct priority_queue *queue);

static const struct priority_queue_vtable fibonacci_heap_vtable = {
    fibonacci_heap_destroy,
    fibonacci_heap_push,
    fibonacci_heap_peek,
    fibonacci_heap_pop,
    fibonacci_heap_size,
    fibonacci_heap_empty
};

static struct fibonacci_heap *fibonacci_heap_from_queue(
    struct priority_queue *queue
)
{
    return (struct fibonacci_heap *)queue;
}

static const struct fibonacci_heap *fibonacci_heap_from_const_queue(
    const struct priority_queue *queue
)
{
    return (const struct fibonacci_heap *)queue;
}

static struct fibonacci_heap_node *fibonacci_heap_node_create(void *item)
{
    struct fibonacci_heap_node *node;

    node = malloc(sizeof(*node));
    if (node == NULL)
        return NULL;

    node->item = item;
    node->parent = NULL;
    node->child = NULL;
    node->left = node;
    node->right = node;
    node->degree = 0;
    node->marked = 0;

    return node;
}

static void fibonacci_heap_list_insert_after(
    struct fibonacci_heap_node *position,
    struct fibonacci_heap_node *node
)
{
    node->left = position;
    node->right = position->right;
    position->right->left = node;
    position->right = node;
}

static void fibonacci_heap_list_remove(struct fibonacci_heap_node *node)
{
    node->left->right = node->right;
    node->right->left = node->left;
    node->left = node;
    node->right = node;
}

static void fibonacci_heap_add_root(
    struct fibonacci_heap *heap,
    struct fibonacci_heap_node *node
)
{
    node->parent = NULL;
    node->marked = 0;

    if (heap->minimum == NULL) {
        node->left = node;
        node->right = node;
        heap->minimum = node;
        return;
    }

    fibonacci_heap_list_insert_after(heap->minimum, node);
    if (heap->base.cmp(node->item, heap->minimum->item) < 0)
        heap->minimum = node;
}

static void fibonacci_heap_add_child(
    struct fibonacci_heap_node *parent,
    struct fibonacci_heap_node *child
)
{
    child->parent = parent;
    child->marked = 0;

    if (parent->child == NULL) {
        child->left = child;
        child->right = child;
        parent->child = child;
    } else {
        fibonacci_heap_list_insert_after(parent->child, child);
    }

    parent->degree++;
}

static void fibonacci_heap_link(
    struct fibonacci_heap_node *child,
    struct fibonacci_heap_node *parent
)
{
    fibonacci_heap_add_child(parent, child);
}

static size_t fibonacci_heap_list_count(struct fibonacci_heap_node *node)
{
    struct fibonacci_heap_node *current;
    size_t count = 0;

    if (node == NULL)
        return 0;

    current = node;
    do {
        count++;
        current = current->right;
    } while (current != node);

    return count;
}

static void fibonacci_heap_update_minimum(struct fibonacci_heap *heap)
{
    struct fibonacci_heap_node *start;
    struct fibonacci_heap_node *current;

    if (heap->minimum == NULL)
        return;

    start = heap->minimum;
    current = start->right;
    while (current != start) {
        if (heap->base.cmp(current->item, heap->minimum->item) < 0)
            heap->minimum = current;
        current = current->right;
    }
}

static void fibonacci_heap_consolidate(struct fibonacci_heap *heap)
{
    struct fibonacci_heap_node **roots;
    struct fibonacci_heap_node **by_degree;
    struct fibonacci_heap_node *current;
    size_t root_count;
    size_t degree_capacity;
    size_t i;

    root_count = fibonacci_heap_list_count(heap->minimum);
    if (root_count == 0)
        return;

    roots = malloc(root_count * sizeof(*roots));
    if (roots == NULL) {
        fibonacci_heap_update_minimum(heap);
        return;
    }

    degree_capacity = heap->size + 1;
    by_degree = calloc(degree_capacity, sizeof(*by_degree));
    if (by_degree == NULL) {
        free(roots);
        fibonacci_heap_update_minimum(heap);
        return;
    }

    current = heap->minimum;
    for (i = 0; i < root_count; i++) {
        roots[i] = current;
        current = current->right;
    }

    for (i = 0; i < root_count; i++) {
        roots[i]->left = roots[i];
        roots[i]->right = roots[i];
    }
    heap->minimum = NULL;

    for (i = 0; i < root_count; i++) {
        struct fibonacci_heap_node *node = roots[i];
        size_t degree = node->degree;

        while (by_degree[degree] != NULL) {
            struct fibonacci_heap_node *other = by_degree[degree];

            if (heap->base.cmp(other->item, node->item) < 0) {
                struct fibonacci_heap_node *tmp = node;
                node = other;
                other = tmp;
            }

            by_degree[degree] = NULL;
            fibonacci_heap_link(other, node);
            degree = node->degree;
        }

        by_degree[degree] = node;
    }

    for (i = 0; i < degree_capacity; i++) {
        if (by_degree[i] != NULL)
            fibonacci_heap_add_root(heap, by_degree[i]);
    }

    free(by_degree);
    free(roots);
}

static void fibonacci_heap_destroy_nodes(struct fibonacci_heap_node *node)
{
    struct fibonacci_heap_node *current;
    struct fibonacci_heap_node *next;
    size_t count;
    size_t i;

    if (node == NULL)
        return;

    count = fibonacci_heap_list_count(node);
    current = node;
    for (i = 0; i < count; i++) {
        next = current->right;
        fibonacci_heap_destroy_nodes(current->child);
        free(current);
        current = next;
    }
}

struct priority_queue *fibonacci_heap_create(priority_queue_cmp_fn cmp)
{
    struct fibonacci_heap *heap;

    heap = malloc(sizeof(*heap));
    if (heap == NULL)
        return NULL;

    priority_queue_init(&heap->base, &fibonacci_heap_vtable, cmp);
    heap->minimum = NULL;
    heap->size = 0;

    return &heap->base;
}

static void fibonacci_heap_destroy(struct priority_queue *queue)
{
    struct fibonacci_heap *heap = fibonacci_heap_from_queue(queue);

    fibonacci_heap_destroy_nodes(heap->minimum);
    free(heap);
}

static int fibonacci_heap_push(struct priority_queue *queue, void *item)
{
    struct fibonacci_heap *heap = fibonacci_heap_from_queue(queue);
    struct fibonacci_heap_node *node;

    node = fibonacci_heap_node_create(item);
    if (node == NULL)
        return -1;

    fibonacci_heap_add_root(heap, node);
    heap->size++;

    return 0;
}

static void *fibonacci_heap_peek(const struct priority_queue *queue)
{
    const struct fibonacci_heap *heap =
        fibonacci_heap_from_const_queue(queue);

    if (heap->minimum == NULL)
        return NULL;

    return heap->minimum->item;
}

static void *fibonacci_heap_pop(struct priority_queue *queue)
{
    struct fibonacci_heap *heap = fibonacci_heap_from_queue(queue);
    struct fibonacci_heap_node *minimum = heap->minimum;
    void *item;
    size_t child_count;
    size_t i;

    if (minimum == NULL)
        return NULL;

    item = minimum->item;

    child_count = minimum->degree;
    for (i = 0; i < child_count; i++) {
        struct fibonacci_heap_node *child = minimum->child;

        if (child->right == child)
            minimum->child = NULL;
        else
            minimum->child = child->right;

        fibonacci_heap_list_remove(child);
        minimum->degree--;
        fibonacci_heap_add_root(heap, child);
    }

    if (minimum->right == minimum) {
        heap->minimum = NULL;
    } else {
        heap->minimum = minimum->right;
        fibonacci_heap_list_remove(minimum);
    }

    heap->size--;
    if (heap->minimum != NULL)
        fibonacci_heap_consolidate(heap);

    free(minimum);
    return item;
}

static size_t fibonacci_heap_size(const struct priority_queue *queue)
{
    return fibonacci_heap_from_const_queue(queue)->size;
}

static int fibonacci_heap_empty(const struct priority_queue *queue)
{
    return fibonacci_heap_size(queue) == 0;
}
