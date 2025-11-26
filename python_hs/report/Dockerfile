# syntax=docker/dockerfile:1-labs

# non-stable syntax used for --parents flag

FROM hs

ENV UV_COMPILE_BYTECODE=true

COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /uvx /bin/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install MACS3 kaggle datasets

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt install -y \
        bc \
        bwa \
        samtools \
        hyperfine \
        default-jre \
        curl \
        unzip \
        ffmpeg \
        unrar-free \
        jq \
        sox \
        python-is-python3 \
        seqtk \
        sra-toolkit

WORKDIR /srv/hs/python_hs/report/

COPY --parents tools/ .
COPY run_specific_benchmark.sh .
COPY --parents benchmarks .

ENV PATH="/srv/hs/.venv/bin/:/srv/hs/python_hs/report/tools/:${PATH}"
ENV PYTHONPATH="/srv/hs/python_hs/:${PYTHONPATH:-}"
