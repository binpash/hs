FROM ezri/hs

RUN apt-get update && apt-get install -y git \
    gcc \
    make \
    pkg-config

RUN git clone https://github.com/redis/redis && \
    cd redis && \
    git checkout d96f47cf06b1cc24b82109e0e87ac5428517525a && \
    make .make-prerequisites

COPY redis_build.sh /redis/redis_build.sh