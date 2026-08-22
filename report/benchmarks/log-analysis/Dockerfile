from hs

RUN apt-get update
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/log-analysis
RUN bash ./report/benchmarks/log-analysis/setup
