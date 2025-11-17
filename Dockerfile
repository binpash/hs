FROM debian:12

RUN mkdir -p /srv/hs
WORKDIR /srv/hs
SHELL ["/bin/bash", "-c"]
RUN apt update
RUN apt install -y vim sudo git python3 python3.11-venv strace wget make python3-cram file graphviz libtool python3-matplotlib libcap2-bin util-linux
# pash distro deps
RUN apt install -y bc curl graphviz bsdmainutils libffi-dev locales locales-all netcat-openbsd pkg-config procps python3-pip python3-setuptools python3-testresources wamerican-insane
# try deps
RUN apt install -y expect mergerfs attr
RUN git config --global --add safe.directory /srv/hs
COPY . .
# Explicitly copy deps/pash to ensure local changes (not submodule) are used
COPY deps/pash /srv/hs/deps/pash
RUN python3 -m venv .venv
RUN source .venv/bin/activate
ENV PASH_SPEC_TOP=/srv/hs
ENV PASH_TOP=/srv/hs/deps/pash
WORKDIR /srv/hs/deps/try
RUN make -C utils
RUN mv utils/try-commit /bin
RUN mv utils/try-summary /bin
WORKDIR /srv/hs/deps/pash
RUN sed -i 's/python3 -m pip install -U --force-reinstall pip/python3 -m pip install --break-system-packages -U --force-reinstall pip/' ./scripts/setup-pash.sh && \
    PIP_BREAK_SYSTEM_PACKAGES=1 ./scripts/setup-pash.sh
WORKDIR /srv/hs
RUN python3 scripts/patch_pash.py
WORKDIR /srv/hs
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/srv/hs/entrypoint.sh"]
