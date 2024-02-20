FROM ghcr.io/ezrizhu/teraseq:latest
# Init Teraseq
VOLUME ["/root/TERA-Seq_manuscript/samples"]
WORKDIR /root/TERA-Seq_manuscript
COPY report/benchmarks/teraseq .
RUN mv -f ./activate.d/* /root/miniconda3/envs/teraseq/etc/conda/activate.d
RUN mv -f ./deactivate.d/* /root/miniconda3/envs/teraseq/etc/conda/deactivate.d
WORKDIR /root/TERA-Seq_manuscript/data
RUN ./run.sh
# Init hs
RUN mkdir -p /srv/hs
WORKDIR /srv/hs
COPY . .
SHELL ["/bin/bash", "-c"]
RUN apt update
RUN apt install -y vim sudo git python3 python3-venv strace wget
RUN git config --global --add safe.directory /srv
RUN python3 -m venv .venv
RUN source .venv/bin/activate
RUN scripts/install_deps_ubuntu20.sh
# back to teraseq
WORKDIR /root/TERA-Seq_manuscript/samples
# init venv
RUN chmod +x entrypoint.sh
ENTRYPOINT ["/srv/hs/entrypoint.sh"]
