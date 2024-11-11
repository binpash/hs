from hs

WORKDIR /srv/hs
RUN apt update && apt install -y unzip
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/dgsh
RUN ./report/benchmarks/dgsh/setup
