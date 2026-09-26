# hs/sklearn: the base image plus the Python packages the benchmark's scripts
# import, installed into hs's own venv. This suite generates its data at run
# time, so ./setup has nothing to download. Versions are ones with prebuilt
# wheels for the image's Python (3.13): without them pip builds scikit-learn
# from source and fails.
FROM hs
WORKDIR /srv/hs
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/sklearn
RUN .venv/bin/pip install -r report/benchmarks/sklearn/requirements.txt
