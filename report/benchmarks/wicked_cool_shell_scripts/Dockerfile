FROM hs

RUN apt update
RUN apt install -y time

RUN rm -r /srv/hs/report/benchmarks/wicked_cool_shell_scripts
COPY . /srv/hs/report/benchmarks/wicked_cool_shell_scripts
WORKDIR /srv/hs/report/benchmarks/wicked_cool_shell_scripts
