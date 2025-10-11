FROM hs

WORKDIR /srv/hs

RUN apt install -y \
    bwa \
    samtools \
    trimmomatic \
    hyperfine

RUN source .venv/bin/activate && pip install MACS3

WORKDIR /srv/hs/python_hs/benchmarks/bioinfo-automine
