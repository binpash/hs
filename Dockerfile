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
        expect mergerfs attr \
        # trace_v3 / eBPF deps
        gcc clang llvm libbpf-dev zlib1g-dev libelf-dev autopoint flex bison gawk

# Install Rust and build trace_v3
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path
ENV PATH="/root/.cargo/bin:${PATH}"
RUN git clone https://github.com/binpash/trace_v3.git /opt/trace_v3
RUN --mount=type=cache,target=/root/.cargo/registry \
    cd /opt/trace_v3 && cargo build --release && \
    install -o root -m 4755 target/release/trace_v3 /usr/local/bin/trace_v3
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
