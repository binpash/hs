# syntax=docker/dockerfile:1-labs

# non-stable syntax used for --parents flag

FROM hs

ENV UV_BREAK_SYSTEM_PACKAGES=true
ENV UV_SYSTEM_PYTHON=true

COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /uvx /bin/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install MACS3

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt update \
    && apt install -y \
        bwa \
        samtools \
        hyperfine \
        default-jre \
        curl \
        unzip \
        ffmpeg \
        unrar-free \
        jq

WORKDIR /srv/hs/python_hs/report/

COPY --parents benchmarks tools run_specific_benchmark.sh .

RUN curl -L https://github.com/usadellab/Trimmomatic/releases/download/v0.40/Trimmomatic-0.40.zip -o Trimmomatic.zip \
    && unzip Trimmomatic.zip -d trimmomatic \
    && mv trimmomatic/trimmomatic-*.jar tools/trimmomatic.jar \
    && rm -r Trimmomatic.zip trimmomatic/

RUN curl -L https://www.agap-ge2pop.org/wp-content/uploads/macse/releases/macse_v1.01b.jar -o tools/macse_v1.01b.jar 

ENV PATH="/srv/hs/python_hs/report/tools/:${PATH}"
ENV PYTHONPATH="/srv/hs/python_hs/:${PYTHONPATH:-}"
