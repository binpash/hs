FROM hs

RUN apt update
RUN apt install -y gcc libtirpc-dev
ENV CPATH="$(pwd)/include:$(pwd)/lib/dialects/linux:$(pwd)/lib:/usr/include/tirpc:$(pwd)/src"

WORKDIR /root

RUN git clone https://github.com/lsof-org/lsof.git
WORKDIR /root/lsof
RUN git checkout 005e014e1abdadb2493d8b3ce87b37a2c0a2351d
RUN ./Configure -n linux

COPY lsof_build.sh lsof_build.sh
RUN chmod +x lsof_build.sh