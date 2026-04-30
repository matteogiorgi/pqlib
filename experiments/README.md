# experiments

This directory contains manual Python experiments that are useful for exploring
prediction quality on larger inputs, but are too expensive or data-dependent for
the default test suite.

The scripts here may use files such as DIMACS road-network graphs and should be
run explicitly by a developer.  They are not part of the public pqlib API.

`road_network_experiment.py` can write structured outputs:

```sh
python3 experiments/road_network_experiment.py graphs/dimacs/USA-road-d.NY.gr \
  --sources 1,1000,10000 \
  --summary-json experiments/results/ny-summary.json \
  --push-trace-csv experiments/results/ny-push-trace.csv
```

Repository-local DIMACS graph datasets live under `graphs/dimacs/`, so the New
York road network can also be referenced as:

```sh
python3 experiments/road_network_experiment.py graphs/dimacs/USA-road-d.NY.gr
```

The JSON file contains the aggregate summary and per-run statistics.  The CSV
file contains one row per priority-queue push and can be large on full road
networks.
