FROM hs

RUN apt update
RUN apt install -y time

RUN mkdir -p /srv/hs/report/benchmarks/wicked_cool_shell_scripts
COPY . /srv/hs/report/benchmarks/wicked_cool_shell_scripts
WORKDIR /srv/hs/report/benchmarks/wicked_cool_shell_scripts
