FROM ezri/hs

RUN apt-get update && apt-get install -y git \
    gcc \
    make \
    libncurses-dev \
    libsm-dev \
    libice-dev \
    libxt-dev \
    libx11-dev \
    libxdmcp-dev \
    libselinux-dev

RUN git clone https://github.com/vim/vim.git && \
    cd vim && \
    git checkout b836f631dba2534efd314a8f77439cebc75acd4e && \
    ./configure

COPY vim_build.sh /vim/vim_build.sh