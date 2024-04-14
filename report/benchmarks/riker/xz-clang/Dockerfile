FROM hs

RUN apt-get update && apt-get install -y git \
    gcc

WORKDIR /

RUN git clone https://github.com/xz-mirror/xz && \
    cd xz && \
    git checkout 2327a461e1afce862c22269b80d3517801103c1b

COPY xz-clang_build.sh /xz/xz-clang_build.sh