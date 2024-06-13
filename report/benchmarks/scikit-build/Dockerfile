FROM hs
RUN mkdir -p /srv/hs/report/benchmarks/scikit-build
WORKDIR /srv/hs/report/benchmarks/scikit-build
RUN apt update
RUN git clone https://github.com/scikit-learn/scikit-learn.git
WORKDIR /srv/hs/report/benchmarks/scikit-build/scikit-learn
RUN git checkout 37f544db78503ed1a50da02cbb4f1a4e466fb0a7 # v1.5.0
WORKDIR /srv/hs/report/benchmarks/scikit-build
COPY . .
