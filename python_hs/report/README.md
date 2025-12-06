# Python hS Benchmarks

## Setup
1. Make sure the dependencies are installed: docker and the following packages
   ```
   apt install curl ffmpeg hyperfine
   ```
   Make sure that hyperfine is a new enough version such that it supports the `--conclude` flag;
   if not, install the latest version from the github repository.
   Additional scripts are necessary to download data from their original sources, rather than Zenodo.
   <!-- TODO: Put the datasets on Zenodo --> 
2. Add the following to /etc/sudoers so that the benchmark script can clear the page cache in between runs
```
$USER ALL=(ALL) NOPASSWD: /usr/bin/tee /proc/sys/vm/drop_caches
```

## Example usage

```sh
# to download all the datasets
make download-all
# to download the datasets for and run an individial benchmark
make kaggle-captk-brats-preprocessing

# to download the datasets for and run all benchmarks
make
```

After running a benchmark, the runtimes are in `results/`.

The benchmark runner can also be used directly to run a specific type of a benchmark.
Example:
```bash
# -d 1 enables debugg logging for hS
./benchmark.sh -d 1 spec kaggle-captk-brats-preprocessing
```
