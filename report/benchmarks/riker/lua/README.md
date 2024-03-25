## Running instructions

`git pull ghcr.io/binpash/hs/lua:latest`

Or build it yourself by running `docker build -t hs/lua .` from this directory.

After the container is built, we can bring ourself into the container.

`docker run --privileged -it --rm ghcr.io/binpash/hs/lua:latest /bin/bash`

Please note that the priviledged flag is required for hs to work.

First, cd into the lua directory\
`cd /root/lua-5.4.3`

Run regularly \
`time ./lua_build.sh`

Verify \
`file src/lua`

Cleanup \
`make clean`

Run with hs \
`time /srv/hs/pash-spec.sh lua_build.sh`

Verify \
`file src/lua`
