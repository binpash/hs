FROM hs
RUN mkdir -p /srv/hs/report/benchmarks/git-tests
WORKDIR /srv/hs/report/benchmarks/git-tests
RUN apt update && apt-get install -q -y gettext libsvn-perl apache2 cvs cvsps git gnupg subversion make libssl-dev libcurl4-openssl-dev libexpat-dev wget sudo default-jre tcl tk gettext zlib1g-dev perl-modules liberror-perl libauthen-sasl-perl libemail-valid-perl libio-pty-perl libio-socket-ssl-perl libnet-smtp-ssl-perl libdbd-sqlite3-perl libcgi-pm-perl
RUN git clone https://github.com/git/git.git
WORKDIR /srv/hs/report/benchmarks/git-tests/git
RUN git checkout bea9ecd24b0c3bf06cab4a851694fe09e7e51408 # v2.45.2
RUN make configure && ./configure && make
WORKDIR /srv/hs/report/benchmarks/git-tests
COPY . .
WORKDIR /srv/hs/deps/try
RUN git fetch && git switch commit-utils
