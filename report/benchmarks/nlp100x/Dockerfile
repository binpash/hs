from hs

RUN apt-get update
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/nlp100x
RUN ./report/benchmarks/nlp100x/setup
