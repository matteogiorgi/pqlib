#include <stdlib.h>

#include "heaps/kaplan_heap.h"
#include "priority_queue_internal.h"

/*
 * Simple Fibonacci heap from "Fibonacci Heaps Revisited", exposed in hpqlib as
 * the Kaplan heap backend.
 *
 * Unlike the classic Fibonacci heap backend, this representation keeps a single
 * heap-ordered tree. Insertions use naive links against the root. delete-min
 * removes the root, performs fair links among children with equal rank, then
 * folds the remaining roots back into one tree with naive links.
 */
struct kaplan_heap_node {
    void *item;
    struct kaplan_heap_node *parent;
    struct kaplan_heap_node *child;
    struct kaplan_heap_node *before;
    struct kaplan_heap_node *after;
    size_t rank;
    int marked;
};

struct kaplan_heap {
    struct priority_queue base;
    struct kaplan_heap_node *root;
    size_t size;
};

static void kaplan_heap_destroy(struct priority_queue *queue);
static int kaplan_heap_push(struct priority_queue *queue, void *item);
static void *kaplan_heap_peek(const struct priority_queue *queue);
static void *kaplan_heap_pop(struct priority_queue *queue);
static size_t kaplan_heap_size(const struct priority_queue *queue);
static int kaplan_heap_empty(const struct priority_queue *queue);

static const struct priority_queue_vtable kaplan_heap_vtable = {
    kaplan_heap_destroy,
    kaplan_heap_push,
    kaplan_heap_peek,
    kaplan_heap_pop,
    kaplan_heap_size,
    kaplan_heap_empty
};

static struct kaplan_heap *kaplan_heap_from_queue(struct priority_queue *queue)
{
    return (struct kaplan_heap *)queue;
}

static const struct kaplan_heap *kaplan_heap_from_const_queue(
    const struct priority_queue *queue
)
{
    return (const struct kaplan_heap *)queue;
}

static struct kaplan_heap_node *kaplan_heap_node_create(void *item)
{
    struct kaplan_heap_node *node;

    node = malloc(sizeof(*node));
    if (node == NULL)
        return NULL;

    node->item = item;
    node->parent = NULL;
    node->child = NULL;
    node->before = NULL;
    node->after = NULL;
    node->rank = 0;
    node->marked = 0;

    return node;
}

static void kaplan_heap_add_child(
    struct kaplan_heap_node *parent,
    struct kaplan_heap_node *child
)
{
    child->parent = parent;
    child->before = NULL;
    child->after = parent->child;

    if (parent->child != NULL)
        parent->child->before = child;

    parent->child = child;
}

static struct kaplan_heap_node *kaplan_heap_link(
    struct kaplan_heap *heap,
    struct kaplan_heap_node *left,
    struct kaplan_heap_node *right
)
{
    if (heap->base.cmp(right->item, left->item) < 0) {
        kaplan_heap_add_child(right, left);
        return right;
    }

    kaplan_heap_add_child(left, right);
    return left;
}

static struct kaplan_heap_node *kaplan_heap_fair_link(
    struct kaplan_heap *heap,
    struct kaplan_heap_node *left,
    struct kaplan_heap_node *right
)
{
    struct kaplan_heap_node *root;

    root = kaplan_heap_link(heap, left, right);
    root->rank++;

    return root;
}

static struct kaplan_heap_node *kaplan_heap_link_roots_naively(
    struct kaplan_heap *heap,
    struct kaplan_heap_node *roots
)
{
    struct kaplan_heap_node *root = NULL;

    while (roots != NULL) {
        struct kaplan_heap_node *node = roots;

        roots = roots->after;
        node->parent = NULL;
        node->before = NULL;
        node->after = NULL;

        if (root == NULL)
            root = node;
        else
            root = kaplan_heap_link(heap, root, node);
    }

    return root;
}

static struct kaplan_heap_node *kaplan_heap_consolidate(
    struct kaplan_heap *heap,
    struct kaplan_heap_node *roots
)
{
    struct kaplan_heap_node **by_rank;
    struct kaplan_heap_node *node;
    struct kaplan_heap_node *root = NULL;
    size_t rank_capacity;
    size_t max_rank = 0;
    size_t i;

    if (roots == NULL)
        return NULL;

    rank_capacity = heap->size + 1;
    by_rank = calloc(rank_capacity, sizeof(*by_rank));
    if (by_rank == NULL)
        return kaplan_heap_link_roots_naively(heap, roots);

    node = roots;
    while (node != NULL) {
        struct kaplan_heap_node *next = node->after;
        size_t rank;

        node->parent = NULL;
        node->before = NULL;
        node->after = NULL;

        rank = node->rank;
        while (by_rank[rank] != NULL) {
            struct kaplan_heap_node *other = by_rank[rank];

            by_rank[rank] = NULL;
            node = kaplan_heap_fair_link(heap, node, other);
            rank = node->rank;
        }

        by_rank[rank] = node;
        if (rank > max_rank)
            max_rank = rank;

        node = next;
    }

    for (i = 0; i <= max_rank; i++) {
        if (by_rank[i] == NULL)
            continue;

        if (root == NULL)
            root = by_rank[i];
        else
            root = kaplan_heap_link(heap, root, by_rank[i]);
    }

    free(by_rank);
    return root;
}

static void kaplan_heap_destroy_nodes(struct kaplan_heap_node *node)
{
    while (node != NULL) {
        struct kaplan_heap_node *next = node->after;

        kaplan_heap_destroy_nodes(node->child);
        free(node);
        node = next;
    }
}

struct priority_queue *kaplan_heap_create(priority_queue_cmp_fn cmp)
{
    struct kaplan_heap *heap;

    heap = malloc(sizeof(*heap));
    if (heap == NULL)
        return NULL;

    priority_queue_init(&heap->base, &kaplan_heap_vtable, cmp);
    heap->root = NULL;
    heap->size = 0;

    return &heap->base;
}

static void kaplan_heap_destroy(struct priority_queue *queue)
{
    struct kaplan_heap *heap = kaplan_heap_from_queue(queue);

    kaplan_heap_destroy_nodes(heap->root);
    free(heap);
}

static int kaplan_heap_push(struct priority_queue *queue, void *item)
{
    struct kaplan_heap *heap = kaplan_heap_from_queue(queue);
    struct kaplan_heap_node *node;

    node = kaplan_heap_node_create(item);
    if (node == NULL)
        return -1;

    if (heap->root == NULL)
        heap->root = node;
    else
        heap->root = kaplan_heap_link(heap, heap->root, node);

    heap->size++;
    return 0;
}

static void *kaplan_heap_peek(const struct priority_queue *queue)
{
    const struct kaplan_heap *heap = kaplan_heap_from_const_queue(queue);

    if (heap->root == NULL)
        return NULL;

    return heap->root->item;
}

static void *kaplan_heap_pop(struct priority_queue *queue)
{
    struct kaplan_heap *heap = kaplan_heap_from_queue(queue);
    struct kaplan_heap_node *root = heap->root;
    struct kaplan_heap_node *children;
    void *item;

    if (root == NULL)
        return NULL;

    item = root->item;
    children = root->child;
    heap->size--;
    heap->root = kaplan_heap_consolidate(heap, children);

    free(root);
    return item;
}

static size_t kaplan_heap_size(const struct priority_queue *queue)
{
    return kaplan_heap_from_const_queue(queue)->size;
}

static int kaplan_heap_empty(const struct priority_queue *queue)
{
    return kaplan_heap_size(queue) == 0;
}
