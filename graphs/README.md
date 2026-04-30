# Graph Datasets

This directory is reserved for local graph datasets used in manual checks and
future benchmarks. Dataset files are intentionally not tracked by git.

The current Python loader supports DIMACS shortest-path `.gr` files with lines
like:

```text
c optional comments
p sp <node-count> <arc-count>
a <tail> <head> <weight>
```

Road-network datasets in this format were published for the 9th DIMACS
Implementation Challenge. Put downloaded DIMACS `.gr` files under
`graphs/dimacs/` when you want to run local experiments. The automatic test
suite uses small generated fixtures instead of large dataset files.
