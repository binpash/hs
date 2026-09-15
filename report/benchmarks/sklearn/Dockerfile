# hs/sklearn: the base image plus the Python packages the benchmark's scripts
# import, installed into hs's own venv. This suite generates its data at run
# time, so ./setup has nothing to download.
FROM hs
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/sklearn
RUN .venv/bin/pip install -r report/benchmarks/sklearn/requirements.txt
