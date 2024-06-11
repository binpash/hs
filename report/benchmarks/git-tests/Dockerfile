FROM hs
RUN mkdir -p /srv/hs/report/benchmarks/git-tests
WORKDIR /srv/hs/report/benchmarks/git-tests
RUN apt update && apt-get install gettext -y
RUN git clone https://github.com/git/git.git
WORKDIR /srv/hs/report/benchmarks/git-tests/git
RUN git checkout cd77e87115eab5e80e6b161e7b84a79ba1a12cdc # The eleventh batch
RUN make configure && ./configure && make
WORKDIR /srv/hs/report/benchmarks/git-tests
COPY . .
