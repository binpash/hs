from hs

RUN apt-get update
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/nlp10m
RUN ./report/benchmarks/nlp10m/setup
