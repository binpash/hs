FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
        attr \
        autoconf \
        automake \
        bc \
        build-essential \
        bsdextrautils \
        ca-certificates \
        curl \
        expect \
        file \
        git \
        graphviz \
        jq \
        libcap2-bin \
        libffi-dev \
        libtool \
        locales \
        locales-all \
        m4 \
        make \
        mergerfs \
        netcat-openbsd \
        pkg-config \
        procps \
        python3 \
        python3-cram \
        python3-matplotlib \
        python3-pip \
        python3-setuptools \
        python3-testresources \
        python3-venv \
        python3.12-venv \
        strace \
        sudo \
        util-linux \
        vim \
        wamerican-insane \
        wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv/hs

COPY . .

RUN git config --global --add safe.directory /srv/hs \
    && test -d deps/try/utils \
    && make -C deps/try/utils \
    && install -m 0755 deps/try/utils/try-commit /usr/local/bin/try-commit \
    && install -m 0755 deps/try/utils/try-summary /usr/local/bin/try-summary \
    && make -C executor \
    && python3.12 -m venv python_pkgs \
    && python_pkgs/bin/pip install --upgrade pip \
    && python_pkgs/bin/pip install -r requirements.txt \
    && ln -s python_pkgs .venv

ENV PASH_SPEC_TOP=/srv/hs
ENV PASH_TOP=/srv/hs
ENV ORCH_TOP=/srv/hs
ENV PATH="/srv/hs:${PATH}"

ENTRYPOINT ["/srv/hs/entrypoint.sh"]
