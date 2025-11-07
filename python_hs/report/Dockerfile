# syntax=docker/dockerfile:1-labs

# non-stable syntax used for --parents flag

FROM hs

# Fix permissions, so we can run as a non root user
# so the results aren't owned by root
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN groupadd -g ${GROUP_ID} hs && \
    useradd -u ${USER_ID} -g ${GROUP_ID} -m hs && \
    chown -R hs:hs /srv/hs/

RUN source .venv/bin/activate && pip install MACS3

RUN apt update \
    && apt install -y \
        bwa \
        samtools \
        hyperfine \
        default-jre \
        curl \
        unzip \
        ffmpeg \
    && rm -rf /var/lib/apt/lists/

USER hs

WORKDIR /srv/hs/python_hs/report/

COPY --chown=hs:hs --parents benchmarks tools run_specific_benchmark.sh .

RUN curl -L https://github.com/usadellab/Trimmomatic/releases/download/v0.40/Trimmomatic-0.40.zip -o Trimmomatic.zip \
    && unzip Trimmomatic.zip -d trimmomatic \
    && mv trimmomatic/trimmomatic-*.jar tools/trimmomatic.jar \
    && rm -r Trimmomatic.zip trimmomatic/

RUN curl -L https://www.agap-ge2pop.org/wp-content/uploads/macse/releases/macse_v1.01b.jar -o tools/macse_v1.01b.jar 

ENV PATH="/srv/hs/python_hs/report/tools/:${PATH}"
ENV PYTHONPATH="/srv/hs/python_hs/:${PYTHONPATH:-}"
