FROM hs

WORKDIR /root
COPY 102.sh .
COPY cmd .

RUN for i in $(seq 0 3000); do touch $i.jpg; done
