# hs/nlp100m: the base image plus this suite's scripts. No input data: ./setup
# downloads that onto the host, and run_base mounts it read-only at run time.
FROM hs
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/nlp100m
