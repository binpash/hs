# syntax=docker/dockerfile:1-labs

# non-stable syntax used for --parents flag

FROM hs

RUN source .venv/bin/activate && pip install MACS3

RUN apt update \
    && apt install -y \
        bwa \
        samtools \
        hyperfine \
        default-jre \
        curl \
        unzip \
    && rm -rf /var/lib/apt/lists/

WORKDIR /srv/hs/python_hs/report/

COPY --parents benchmarks tools run_specific_benchmark.sh .

RUN curl -L https://github.com/usadellab/Trimmomatic/releases/download/v0.40/Trimmomatic-0.40.zip -o Trimmomatic.zip \
    && unzip Trimmomatic.zip -d trimmomatic \
    && mv trimmomatic/trimmomatic-*.jar tools/trimmomatic.jar \
    && rm -r Trimmomatic.zip trimmomatic/

RUN curl -L https://www.agap-ge2pop.org/wp-content/uploads/macse/releases/macse_v1.01b.jar -o tools/macse_v1.01b.jar 

ENV PATH="/srv/hs/python_hs/report/tools/:${PATH}"
ENV PYTHONPATH="/srv/hs/python_hs/:${PYTHONPATH:-}"
