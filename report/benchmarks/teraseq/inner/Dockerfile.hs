# syntax=docker/dockerfile:1.7

FROM teraseq20-scripts
RUN mkdir -p /srv/hs
WORKDIR /srv/hs
SHELL ["/bin/bash", "-c"]
# ARG DEBIAN_FRONTEND=noninteractive
RUN ln -fs /usr/share/zoneinfo/America/New_York /etc/localtime
RUN apt update
RUN apt install -y sudo curl git
RUN apt install -y vim strace make python3-cram file graphviz libtool python3-matplotlib libcap2-bin mergerfs lsb-release sudo git python3 wget util-linux build-essential ca-certificates
# hS runtime deps
RUN apt install -y bc curl graphviz bsdmainutils libffi-dev locales locales-all netcat-openbsd pkg-config procps python3-pip python3-setuptools python3-testresources wamerican-insane
# try deps
RUN apt install -y expect mergerfs attr
COPY requirements.txt requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-py312_25.5.1-0-Linux-x86_64.sh -o /tmp/hs-miniconda.sh \
    && bash /tmp/hs-miniconda.sh -b -p /srv/hs/python_pkgs \
    && rm -f /tmp/hs-miniconda.sh \
    && python_pkgs/bin/pip install --upgrade pip \
    && python_pkgs/bin/pip install -r requirements.txt \
    && python_pkgs/bin/conda clean -afy \
    && ln -s python_pkgs .venv

COPY deps/try deps/try
COPY deps/pash deps/pash
RUN --mount=type=cache,target=/root/.cache/pip \
    python_pkgs/bin/pip install -e deps/pash pash-annotations==0.2.4
COPY executor executor
WORKDIR /srv/hs/deps/try
RUN make -C utils
RUN install -m 0755 utils/try-commit /usr/local/bin/try-commit
RUN install -m 0755 utils/try-summary /usr/local/bin/try-summary

WORKDIR /srv/hs
RUN make -C executor

COPY scheduler scheduler
COPY preprocessor preprocessor
COPY jit_runtime jit_runtime
COPY hs hs
COPY pash-spec.sh pash-spec.sh
COPY entrypoint.sh entrypoint.sh
COPY scripts scripts
RUN mkdir -p /srv/hs/report/benchmarks/teraseq
COPY report/benchmarks/teraseq/inner /srv/hs/report/benchmarks/teraseq
RUN install -m 0755 /srv/hs/report/benchmarks/teraseq/pash_wrappers/samtools-sort-merge /usr/local/bin/samtools-sort-merge \
    && install -m 0755 /srv/hs/report/benchmarks/teraseq/pash_wrappers/samtools-sort-name-merge /usr/local/bin/samtools-sort-name-merge

ENV PASH_SPEC_TOP=/srv/hs
ENV PASH_TOP=/srv/hs/deps/pash/src/pash
ENV ORCH_TOP=/srv/hs
ENV PATH="/srv/hs/python_pkgs/bin:/srv/hs:${PATH}"

WORKDIR /srv/hs
RUN chmod +x entrypoint.sh

RUN mv /srv/hs/report/benchmarks/teraseq/annotate-sqlite-with-fastq.R /root/TERA-Seq_manuscript/tools/utils/
RUN python_pkgs/bin/python /srv/hs/report/benchmarks/teraseq/pash_annotations_overlay/install_local_annotations.py /srv/hs/pash-local-annotations
RUN pash --help >/dev/null && test "$(pash -c 'echo hi | cat')" = "hi"
