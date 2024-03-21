FROM ezri/hs

RUN apt-get update && apt-get install -y git \
    gcc \
    make \
    libreadline-dev \
    bsdmainutils

WORKDIR /

RUN git clone https://github.com/lcn2/calc.git && \
    cd calc && \
    git checkout 3d33c6c6f498d4d391918d34c55fe37191db53d8

COPY calc_build.sh /calc/calc_build.sh