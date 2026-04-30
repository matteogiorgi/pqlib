# hpqlib Documentation

hpqlib is a C99 heap-priority-queue library with a small CPython binding.

The documentation is organized as a reference first: public types and functions
are documented with signatures, parameters, return values, ownership rules, and
failure behavior.

## API Reference

- [priority_queue](api/priority_queue.md): public C abstract data type.
- [Heap Implementations](api/implementations.md): available heap backends.
- [Python API](api/python.md): `hpqlib.PriorityQueue` constructor, methods, and
  exceptions.

## Build And Packaging

- [Build And Packaging](building.md): local C builds, Python extension builds,
  wheels, and release workflow.

## Papers

Reference papers used while developing the project live under `docs/papers/`.
