FROM ezri/hs

RUN apt-get update
RUN echo "Europe/London" > /etc/timezone
RUN dpkg-reconfigure -f noninteractive tzdata
RUN apt-get install -y git
RUN apt-get install -y gcc
RUN apt-get install -y tcl8.6
RUN apt-get install -y libtool
RUN apt-get install -y libtool-bin
RUN apt-get install -y libreadline-dev
RUN apt-get install -y tcl8.6-dev
RUN apt-get install -y vim

RUN git clone https://github.com/sqlite/sqlite && cd sqlite && git checkout c1cace0832fa2af5ab8315e217d708c09d586425
RUN ./sqlite/configure

COPY sqlite_build.sh /sqlite/sqlite_build.sh