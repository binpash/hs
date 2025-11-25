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

COPY --parents tools run_specific_benchmark.sh .

RUN curl -L https://github.com/usadellab/Trimmomatic/releases/download/v0.40/Trimmomatic-0.40.zip -o Trimmomatic.zip \
    && unzip Trimmomatic.zip -d trimmomatic \
    && mv trimmomatic/trimmomatic-*.jar tools/trimmomatic.jar \
    && rm -r Trimmomatic.zip trimmomatic/

RUN curl -L https://www.agap-ge2pop.org/wp-content/uploads/macse/releases/macse_v1.01b.jar -o tools/macse_v1.01b.jar

COPY --parents benchmarks .

ENV PATH="/srv/hs/.venv/bin/:/srv/hs/python_hs/report/tools/:${PATH}"
ENV PYTHONPATH="/srv/hs/python_hs/:${PYTHONPATH:-}"
