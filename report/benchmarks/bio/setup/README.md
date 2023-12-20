# Bio Benchmark

## Prerequisites
- `wget` for downloading files
- `dpkg` for package management
- `samtools` (The script will attempt to install it if not present)

## Usage
To run the script, navigate to its directory and use the following command:

```bash
./bio_benchmark_setup.sh [options]
```

### Options
- `-i [file]`: Specify a custom input file. Default is `input_full.txt` located in `$PASH_SPEC_TOP/report/benchmarks/bio/setup/`.
- `-c`: Clean up the environment. This removes all downloaded `.bam` and `.sam` files and the output directory.

### Input File Format
The input file should contain lines in the following format:

```
[Population] [Sample] [URL]
```

For example:

```
CHS HG00614 ftp://ftp.example.com/data/HG00614.bam
```

### Examples
- To run with the default input file:
  ```bash
  ./bio_benchmark_setup.sh
  ```
- To run with a custom input file:
  ```bash
  ./bio_benchmark_setup.sh -i /path/to/custom/input.txt
  ```
- To clean up downloaded files:
  ```bash
  ./bio_benchmark_setup.sh -c
  ```
