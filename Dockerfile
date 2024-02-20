FROM debian:12

RUN mkdir -p /srv/hs
WORKDIR /srv/hs
COPY . .
SHELL ["/bin/bash", "-c"]
RUN apt update
RUN apt install -y vim sudo git python3 python3.11-venv strace wget
RUN git config --global --add safe.directory /srv
RUN python3 -m venv .venv
RUN source .venv/bin/activate
RUN scripts/install_deps_ubuntu20.sh
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/srv/hs/entrypoint.sh"]
