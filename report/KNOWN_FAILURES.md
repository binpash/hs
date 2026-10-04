# Benchmarks that fail for reasons other than hs

These fail the sh-vs-hs comparison, or never produce a result, because of the
benchmark itself or its environment, not because hs computes something wrong.
Leave them out of runs (e.g. drop them from the `report/bench -f` list).

| Benchmark | Why it fails |
|---|---|
| `nlp/6_7` (and the same script in `nlp10x`, `nlp100x`, `nlp1000x`, `nlp1m`, `nlp10m`, `nlp100m`) | Plain sh exits 1: the script ends with `grep -vc`, which exits 1 whenever it counts 0 lines. The harness does not accept a nonzero sh exit as a baseline. sh and hs agree on outputs and status. |
| `dgsh/3` | Line 106 is `find "$@" ...`, and the benchmark is run with no arguments, so it searches the working directory (the hs checkout) instead of `$REPO_DIR`. sh and hs find the same files in a different order (find returns directory-read order, which differs on hs's overlay sandbox), and `file2.txt`, `file3.txt`, `file4.txt` are built from that list. |
| `dgsh/18` | `file1.txt` and the last line of stdout are `df -h` free space, which changes between the sh and hs runs. |
| `wicked_cool_shell_scripts/37` | Prints `df -k`: live free space, and under hs the mounts of its sandbox rather than the system's. |
| `wicked_cool_shell_scripts/40`, `42`, `50`, `51`, `52`, `102` | Never produce a result. Their `run` scripts predate `run_benchmark.py`: they accept only a single `--target` value and exit with `Unknown parameter passed: hs`. |
| `wicked_cool_shell_scripts/41` | Has no `run` script at all, and calls `passwd`, which prompts on a terminal. |
| `log-analysis/medium` | Produced no result on CloudLab; cause not yet known. |
