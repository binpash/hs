# syntax=docker/dockerfile:1-labs

# non-stable syntax used for --parents flag

FROM hs

ENV UV_COMPILE_BYTECODE=true

COPY --from=ghcr.io/astral-sh/uv:0.9.8 /uv /uvx /bin/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install MACS3 kaggle

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
        python-is-python3

WORKDIR /srv/hs/python_hs/report/

COPY --parents squashfs-root/ benchmarks tools run_specific_benchmark.sh .

RUN curl -L https://github.com/usadellab/Trimmomatic/releases/download/v0.40/Trimmomatic-0.40.zip -o Trimmomatic.zip \
    && unzip Trimmomatic.zip -d trimmomatic \
    && mv trimmomatic/trimmomatic-*.jar tools/trimmomatic.jar \
    && rm -r Trimmomatic.zip trimmomatic/

# IDEA: Copy the app image from the docker?
RUN curl -L https://www.agap-ge2pop.org/wp-content/uploads/macse/releases/macse_v1.01b.jar -o tools/macse_v1.01b.jar
# RUN curl -L https://www.nitrc.org/frs/downloadlink.php/11778 -o captk_installer.bin \
#     && chmod +x captk_installer.bin \
#     && ./captk_installer.bin --app-image-extract


ENV PATH="/srv/hs/.venv/bin/:/srv/hs/python_hs/report/squashfs-root/usr/bin:/srv/hs/python_hs/report/tools/:${PATH}"
ENV PYTHONPATH="/srv/hs/python_hs/:${PYTHONPATH:-}"
