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
# Sandbox base for hs (see executor/executor_util.py); the entrypoint mounts
# a tmpfs here so overlay upperdirs don't land on the container's overlayfs
# rootfs (not a valid overlay upper) or on /dev/shm (noexec, 64MB cap).
RUN mkdir -m 1777 /hs-sandbox
ENV PASH_SPEC_TOP=/srv/hs
ENV PASH_TOP=/srv/hs/deps/pash
# pash, try, fstrace
COPY deps/ deps/
WORKDIR /srv/hs/deps/try
RUN make -C utils
RUN mv utils/try-commit /bin
RUN mv utils/try-summary /bin
WORKDIR /srv/hs/deps/fstrace
RUN ./install.sh
# WORKDIR /srv/hs/deps/pash
# RUN ./scripts/setup-pash.sh
WORKDIR /srv/hs
RUN python3 -m venv .venv
COPY . .
RUN make -C executor
# libbash/libdash compile a bundled bash-5.2, whose lib/termcap/tparam.c calls
# write() without including <unistd.h>. GCC 14 (which trixie now ships) makes
# implicit function declarations a hard error rather than a warning, so the
# wheel fails to build. Demote it back to a warning; configure propagates
# CFLAGS into the sub-makes. Keep -g -O2, the defaults configure would pick.
RUN CFLAGS="-g -O2 -Wno-implicit-function-declaration" \
    .venv/bin/pip install -r requirements.txt
ENTRYPOINT ["/srv/hs/entrypoint.sh"]
