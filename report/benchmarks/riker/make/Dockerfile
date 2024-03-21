FROM ezri/hs

RUN apt-get update && apt-get install -y wget \
    gcc \
    make

WORKDIR /

RUN wget http://ftp.gnu.org/gnu/make/make-4.3.tar.gz && \
    tar xzf make-4.3.tar.gz && \
    rm make-4.3.tar.gz && \
    cd make-4.3 && \
    ./configure && \
    make clean

COPY make_build.sh /make-4.3/make_build.sh