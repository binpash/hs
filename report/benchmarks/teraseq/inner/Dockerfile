# syntax=docker/dockerfile:1.7

FROM ghcr.io/binpash/teraseq20:latest
WORKDIR /root/TERA-Seq_manuscript
COPY . .
COPY activate.d activate.d
COPY deactivate.d deactivate.d
COPY data/run.sh run-data.sh
RUN mv -f activate.d/* /root/miniconda3/envs/teraseq/etc/conda/activate.d
RUN mv -f deactivate.d/* /root/miniconda3/envs/teraseq/etc/conda/deactivate.d
