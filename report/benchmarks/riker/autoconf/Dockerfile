FROM hs

RUN apt-get update && apt-get install -y wget \
    make \
    m4 \
    perl

WORKDIR /root

RUN wget https://ftp.gnu.org/gnu/autoconf/autoconf-2.69.tar.gz && \
    tar xzvf autoconf-2.69.tar.gz && \
    rm autoconf-2.69.tar.gz && \
    ./autoconf-2.69/configure

COPY autoconf_build.sh /root/autoconf-2.69/autoconf_build.sh
RUN chmod +x /root/autoconf-2.69/autoconf_build.sh
WORKDIR /root/autoconf-2.69
