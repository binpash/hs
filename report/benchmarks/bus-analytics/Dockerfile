from hs

RUN apt-get update
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/bus-analytics
RUN ./report/benchmarks/bus-analytics/setup
