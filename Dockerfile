FROM debian:trixie

RUN mkdir -p /srv/hs
WORKDIR /srv/hs
SHELL ["/bin/bash", "-c"]

# https://docs.docker.com/build/cache/optimize/#use-cache-mounts
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt install -y \
        # hs deps
        vim sudo git python3 python3-venv strace wget make python3-cram file graphviz libtool python3-matplotlib libcap2-bin util-linux \
        # pash deps
        curl graphviz bsdmainutils libffi-dev locales locales-all netcat-openbsd pkg-config procps python3-pip python3-setuptools python3-testresources wamerican-insane \
        # try deps
        expect mergerfs attr \
        # fstrace / eBPF deps
        gcc clang llvm libbpf-dev zlib1g-dev libelf-dev autopoint flex bison bpftool gawk man-db

RUN git config --global --add safe.directory /srv
ENV PASH_SPEC_TOP=/srv/hs
ENV PASH_TOP=/srv/hs/deps/pash
# pash, try, fstrace
COPY deps/ deps/
COPY .git/ .git/
WORKDIR /srv/hs/deps/try
RUN make -C utils
RUN mv utils/try-commit /bin
RUN mv utils/try-summary /bin
WORKDIR /srv/hs/deps/fstrace
RUN ./install.sh
RUN fstrace install
# WORKDIR /srv/hs/deps/pash
# RUN ./scripts/setup-pash.sh
WORKDIR /srv/hs
RUN python3 -m venv .venv
COPY . .
RUN .venv/bin/pip install -r requirements.txt
ENTRYPOINT ["/srv/hs/entrypoint.sh"]
