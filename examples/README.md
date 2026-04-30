# examples

This directory contains small demonstration programs that show how to use
pqlib from client code.

Examples should be readable before they are exhaustive.  They are useful for
understanding the public API, trying a complete minimal program, and checking
what normal usage looks like outside the library internals.

Code in this directory should generally:

- use only public headers and documented APIs;
- prefer clear setup and output over broad edge-case coverage;
- be suitable for manual execution or quick experimentation;
- avoid becoming the main place where correctness is verified.

Correctness checks and regression coverage belong in `tests/`.
