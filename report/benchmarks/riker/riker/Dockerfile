FROM ubuntu:20.04

RUN apt update
RUN apt install -y clang libcereal-dev

WORKDIR /
COPY riker/ /riker
WORKDIR /riker

COPY riker_build.sh /riker/riker_build.sh
RUN chmod +x /riker/riker_build.sh

