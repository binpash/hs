FROM ezri/hs

RUN apt-get update && apt-get install -y gcc \
    make \
    wget

WORKDIR /

RUN wget https://www.lua.org/ftp/lua-5.4.3.tar.gz && \
    tar xzf lua-5.4.3.tar.gz

COPY lua_build.sh /lua-5.4.3/lua_build.sh
