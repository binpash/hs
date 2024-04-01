FROM hs

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

WORKDIR /root

RUN git clone https://github.com/vim/vim.git && \
    cd vim && \
    git checkout b836f631dba2534efd314a8f77439cebc75acd4e && \
    ./configure

COPY vim_build.sh /root/vim/vim_build.sh
RUN chmod +x /root/vim/vim_build.sh
WORKDIR /root/vim
