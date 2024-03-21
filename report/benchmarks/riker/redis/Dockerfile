FROM ezri/hs

RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y make
RUN apt-get install -y gcc
RUN apt-get install -y pkg-config

RUN git clone https://github.com/redis/redis && cd redis && git checkout d96f47cf06b1cc24b82109e0e87ac5428517525a
RUN make .make-prerequisites

# and copy redis_build.sh into the Dockerfile under the redis directory
COPY redis_build.sh /redis/redis_build.sh