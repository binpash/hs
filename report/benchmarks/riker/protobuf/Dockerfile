FROM hs

WORKDIR /

RUN apt-get update && apt-get install -y git make gcc autoconf libtool g++

RUN git clone https://github.com/protocolbuffers/protobuf.git
WORKDIR /protobuf
RUN git checkout 909a0f36a10075c4b4bc70fdee2c7e32dd612a72

RUN autoreconf -i
RUN ./autogen.sh
RUN test -f Makefile || ./configure
RUN make clean

COPY protobuf_build.sh /protobuf/protobuf_build.sh
RUN chmod +x /protobuf/protobuf_build.sh

sha1sum src/protoc 