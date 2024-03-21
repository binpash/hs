FROM ezri/hs

RUN apt-get update && apt-get install -y wget \
    make \
    m4 \
    perl

WORKDIR /

RUN wget https://ftp.gnu.org/gnu/autoconf/autoconf-2.69.tar.gz && \
    tar xzvf autoconf-2.69.tar.gz && \
    rm autoconf-2.69.tar.gz && \
    ./autoconf-2.69/configure

COPY autoconf_build.sh /autoconf-2.69/autoconf_build.sh