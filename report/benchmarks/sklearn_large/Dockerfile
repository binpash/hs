from hs

RUN apt-get update
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/sklearn_large
RUN ./report/benchmarks/sklearn_large/setup
