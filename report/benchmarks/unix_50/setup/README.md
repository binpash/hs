# Unix50 Benchmark

## Setup
Run the setup script to download the inputs and generate larger input files:

```bash
./report/benchmarks/unix_50/setup [options]
```

### Options
- `-s`: Generate small-size inputs.
- `-f`: Generate full-size inputs by replicating existing files 100 times.
- `-g`: Generate full-size inputs to reach approximately 1GB file size.
- `-d`: Download the dataset from the specified source and unzip it in the download directory.

### Examples
- To set up small inputs:
  ```bash
  ./setup_unix50.sh -s
  ```
- To download and prepare full-size inputs:
  ```bash
  ./setup_unix50.sh -df
  ```
