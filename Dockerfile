FROM debian:12

RUN mkdir -p /srv/hs
WORKDIR /srv/hs
SHELL ["/bin/bash", "-c"]

# https://docs.docker.com/build/cache/optimize/#use-cache-mounts
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt install -y \
        # hs deps
        vim sudo git python3 python3.11-venv strace wget make python3-cram file graphviz libtool python3-matplotlib libcap2-bin util-linux \
        # pash deps
        curl graphviz bsdmainutils libffi-dev locales locales-all netcat-openbsd pkg-config procps python3-pip python3-setuptools python3-testresources wamerican-insane \
        # try deps
        expect mergerfs attr
RUN git config --global --add safe.directory /srv
ENV PASH_SPEC_TOP=/srv/hs
ENV PASH_TOP=/srv/hs/deps/pash
# pash, try
COPY deps/ deps/
WORKDIR /srv/hs/deps/try
RUN make -C utils
RUN mv utils/try-commit /bin
RUN mv utils/try-summary /bin
# WORKDIR /srv/hs/deps/pash
# RUN ./scripts/setup-pash.sh
WORKDIR /srv/hs
RUN python3 -m venv .venv
COPY . .
ENTRYPOINT ["/srv/hs/entrypoint.sh"]
