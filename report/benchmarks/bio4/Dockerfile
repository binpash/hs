# hs/bio4: the base image plus samtools (the benchmark) and aria2 (what setup
# downloads the BAMs with). No input data: ./setup [-i small/list] downloads it
# onto the host, and run_base mounts it read-only at run time.
FROM hs
WORKDIR /srv/hs
RUN apt-get update && apt-get install -y --no-install-recommends samtools time aria2 \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/bio4
