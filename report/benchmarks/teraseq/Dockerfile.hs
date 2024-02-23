FROM ezri/teraseq20-data
RUN mkdir -p /srv/hs
WORKDIR /srv/hs
COPY . .
SHELL ["/bin/bash", "-c"]
ARG DEBIAN_FRONTEND=noninteractive
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime
RUN apt update
RUN apt install -y sudo curl git
ENV PASH_SPEC_TOP=/srv/hs
ENV PASH_TOP=/srv/hs/deps/pash
RUN git submodule update --init --recursive
WORKDIR /srv/hs/deps/pash
RUN conda install -y -c anaconda python=3.11
RUN apt install -y vim strace make python3-cram file graphviz libtool python3-matplotlib libcap2-bin mergerfs lsb-release
RUN scripts/distro-deps.sh
RUN scripts/setup-pash.sh
WORKDIR /srv/hs/deps/try
RUN ./setup.sh
WORKDIR /srv/hs
RUN chmod +x entrypoint.sh
WORKDIR /root/TERA-Seq_manuscript/samples
