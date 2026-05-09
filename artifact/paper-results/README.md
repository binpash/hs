# Paper Results and Plotting Artifacts

This directory is a self-contained snapshot of the paper-result materials,
without requiring the nested paper repository or its Git history.

## Contents

- `bin/`: plotting and analysis scripts.
- `data/`: precomputed CSV, JSON, and log-derived data used by the plotting scripts.
- `img/`: generated figures used by the paper.
- `tables/`: generated or auxiliary table material copied from the paper tree.
- `requirements.txt`: Python packages needed by the plotting scripts.

## Recreating Representative Figures

Run these commands from this directory:

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt

python bin/generate_pash_vs_hs_barplots.py
python bin/mispeculation.py
python bin/open_heavy.py
python bin/varying_window.py
python bin/python_performance_plot.py
```

Expected outputs are written under `img/`. The most relevant mappings are:

| Paper result | Script | Primary input | Output |
| --- | --- | --- | --- |
| Overall hS and PaSh performance | `bin/generate_pash_vs_hs_barplots.py` | `data/results_w30_updated.csv` | `img/hs_pash_plot.pdf` |
| Mis-speculation and execution trace | `bin/mispeculation.py` | `data/misspeculation_log/` | `img/execution_and_misspeculation.pdf` |
| I/O-heavy overheads | `bin/open_heavy.py` | `data/io_heavy/`, `data/open_heavy/` | `img/open_heavy.pdf` |
| Varying speculation window sizes | `bin/varying_window.py` | `data/hs_window.csv` | `img/varying_window_sizes.pdf` |
| Python frontend results | `bin/python_performance_plot.py` | `data/python_hs_results.json` | `img/python_speedup_bar.pdf` |

The scripts are intended to regenerate the figures from precomputed results, not
to rerun the full experiments. Full benchmark execution is documented from the
repository root in `report/README.md`, `report/all_benchmarks`, and
`python_hs/report/README.md`.
