from hs

RUN apt-get update
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/max_temp
RUN ./report/benchmarks/max_temp/setup
