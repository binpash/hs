FROM debian:12

RUN mkdir -p /srv/hs
WORKDIR /srv/hs
COPY . .
SHELL ["/bin/bash", "-c"]
RUN apt update
RUN apt install -y vim sudo git python3 python3.11-venv strace wget make python3-cram file graphviz libtool python3-matplotlib libcap2-bin mergerfs
RUN git config --global --add safe.directory /srv
RUN python3 -m venv .venv
RUN source .venv/bin/activate
ENV PASH_SPEC_TOP=/srv/hs
ENV PASH_TOP=/srv/hs/deps/pash
RUN git submodule update --init --recursive
WORKDIR /srv/hs/deps/try
RUN ./setup.sh
WORKDIR /srv/hs/deps/pash
RUN ./scripts/distro-deps.sh
RUN ./scripts/setup-pash.sh
WORKDIR /srv/hs
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/srv/hs/entrypoint.sh"]
