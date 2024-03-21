FROM ezri/hs

RUN echo "Europe/London" > /etc/timezone \
    dpkg-reconfigure -f noninteractive tzdata
    apt-get update && apt-get install -y git \
    gcc \
    tcl8.6 \
    libtool \
    libtool-bin \
    libreadline-dev \
    tcl8.6-dev \
    vim

RUN git clone https://github.com/sqlite/sqlite && \
    cd sqlite && \
    git checkout c1cace0832fa2af5ab8315e217d708c09d586425 && \
    ./configure

COPY sqlite_build.sh /sqlite/sqlite_build.sh