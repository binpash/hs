FROM ezri/hs

RUN apt-get update
RUN apt-get install -y git
RUN apt-get install -y make
RUN apt-get install -y gcc
RUN apt-get install -y libncurses-dev
RUN apt-get install -y libsm-dev
RUN apt-get install -y libice-dev
RUN apt-get install -y libxt-dev
RUN apt-get install -y libx11-dev
RUN apt-get install -y libxdmcp-dev
RUN apt-get install -y libselinux-dev

RUN git clone https://github.com/vim/vim.git && cd vim && git checkout b836f631dba2534efd314a8f77439cebc75acd4e
RUN ./configure

COPY vim_build.sh /vim/vim_build.sh