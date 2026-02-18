FROM python:3.12-bookworm

RUN mkdir -p /srv/hs
WORKDIR /srv/hs
SHELL ["/bin/bash", "-c"]

# https://docs.docker.com/build/cache/optimize/#use-cache-mounts
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt install -y \
        # hs deps
        vim sudo git strace wget make file graphviz libtool python3-matplotlib libcap2-bin util-linux \
        # pash deps
        curl graphviz bsdmainutils libffi-dev locales locales-all netcat-openbsd pkg-config procps wamerican-insane \
        # try deps
        expect mergerfs attr
RUN git config --global --add safe.directory /srv
ENV PASH_SPEC_TOP=/srv/hs
ENV PASH_TOP=/srv/hs/deps/pash
# try
COPY deps/try deps/try
WORKDIR /srv/hs/deps/try
RUN make -C utils
RUN mv utils/try-commit /bin
RUN mv utils/try-summary /bin
WORKDIR /srv/hs
RUN python3 -m venv python_pkgs
COPY requirements.txt .
RUN python_pkgs/bin/pip install --upgrade pip \
    && python_pkgs/bin/pip install -r requirements.txt
COPY python_hs/ python_hs/
RUN python_pkgs/bin/pip install python_hs/
COPY . .
RUN cd executor && make clean && make
ENTRYPOINT ["/srv/hs/entrypoint.sh"]
