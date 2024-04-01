FROM hs

RUN apt-get update && apt-get install -y git \
    gcc \
    autotools-dev \
    automake \
    libevent-dev

WORKDIR /root

RUN git clone https://github.com/memcached/memcached.git && \
    cd memcached && \
    git checkout c472369fed5981ba8c004d426cee62d5165c47ca && \
    ./autogen.sh && \
    ./configure --disable-dependency-tracking

COPY memcached_build.sh /root/memcached/memcached_build.sh
RUN chmod +x /root/memcached/memcached_build.sh
WORKDIR /root/memcached
