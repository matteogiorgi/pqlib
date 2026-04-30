# DIMACS Graphs

This directory contains graph datasets in DIMACS shortest-path `.gr` format.

The expected format is:

```text
c optional comments
p sp <node-count> <arc-count>
a <tail> <head> <weight>
```

These files are intended for manual experiments and benchmarks, not for the
default fast test suite.  Python experiments can load them with
`load_dimacs_graph(path)`, which stores the graph as CSR arrays.
