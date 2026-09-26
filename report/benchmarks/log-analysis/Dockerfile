# hs/log-analysis: the base image plus the ITA `recreate` tool the benchmark
# pipes its logs through, built here from the upstream tarball. No input data:
# ./setup downloads the logs onto the host, mounted read-only at run time.
# The tools are 1990s C (no #include <string.h>, implicit int); GCC 14 makes
# those errors, and -fpermissive turns them back into warnings.
FROM hs
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/log-analysis
ARG IN_ROOT=https://atlas-group.cs.brown.edu/data/web-logs/world-cup
RUN cd report/benchmarks/log-analysis \
    && wget -q "$IN_ROOT/WorldCup_tools.tar" && tar -xf WorldCup_tools.tar && rm WorldCup_tools.tar \
    && make -C ita_public_tools CC="gcc -fpermissive" \
    && cp ita_public_tools/bin/recreate ita_public_tools/state/object_mappings.sort .
