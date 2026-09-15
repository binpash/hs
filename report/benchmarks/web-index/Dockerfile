# hs/web-index: the base image plus pandoc 2.2.1, node 18 and the suite's npm
# packages. No input data: ./setup downloads the wikipedia articles onto the
# host, mounted read-only at run time.
FROM hs
WORKDIR /srv/hs
RUN apt-get update && apt-get install -y --no-install-recommends p7zip-full curl wget unzip \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && wget -q "https://github.com/jgm/pandoc/releases/download/2.2.1/pandoc-2.2.1-1-$(dpkg --print-architecture).deb" \
    && dpkg -i "pandoc-2.2.1-1-$(dpkg --print-architecture).deb" && rm "pandoc-2.2.1-1-$(dpkg --print-architecture).deb" \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/web-index
RUN cd report/benchmarks/web-index && npm install
