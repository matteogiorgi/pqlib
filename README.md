# Heaplib

Heaplib is a C library providing multiple priority queue implementations, including *binary heaps*, *Fibonacci heaps*, and *revisited Fibonacci heaps*, with a unified interface for algorithmic experimentation and benchmarking.

The repository contains:

- `binaryheap.h`: the library's public interface;
- `binaryheap.c`: implementation of the generic min-heap based on `void **` and a comparator function;
- `binaryheap_demo.c`: usage demo program;
- `binaryheap_test.c`: automated tests using `assert`;
- `Makefile`: builds the object file and demo, and runs the tests.




#### Useful Commands

- `make`: builds `binaryheap.o`;
- `make run`: builds and runs the demo;
- `make test`: builds and runs the tests;
- `make clean`: removes build artifacts.
