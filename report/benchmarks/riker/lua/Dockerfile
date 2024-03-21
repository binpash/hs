FROM ezri/hs

RUN apt-get update
RUN apt-get install -y gcc
RUN apt-get install -y wget

RUN wget https://www.lua.org/ftp/lua-5.4.3.tar.gz
RUN tar xzf lua-5.4.3.tar.gz

COPY lua_build.sh /lua-5.4.3/lua_build.sh