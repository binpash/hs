from hs

RUN apt-get update
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/nlp1000x
RUN ./report/benchmarks/nlp1000x/setup
