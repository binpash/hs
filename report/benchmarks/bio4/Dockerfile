from hs

RUN apt-get update
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks/bio4
# Which BAM list setup downloads at build time. The default pulls all 25
# samples (~100 GB); pass --build-arg BIO4_INPUT_LIST=small/list for a
# ~700 MB image that can only run the small size.
ARG BIO4_INPUT_LIST=input_full.txt
COPY ./inner/setup report/benchmarks/bio4/setup
COPY ./inner/input_full.txt report/benchmarks/bio4/input_full.txt
COPY ./inner/small/list report/benchmarks/bio4/small/list
COPY ./inner/medium/list report/benchmarks/bio4/medium/list
COPY ./inner/large/list report/benchmarks/bio4/large/list
RUN ./report/benchmarks/bio4/setup -i "$BIO4_INPUT_LIST"
COPY ./inner report/benchmarks/bio4
