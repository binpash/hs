## Running instructions

Build the image `docker build -t hs/ex2 .` from this directory.

Running with HS
`docker run --privileged --rm hs/ex2:latest /bin/bash -c 'time /srv/hs/pash-spec.sh /root/workspace/ex2.sh && sha1sum /root/workspace/htseq_output/SRR10045016-17-18-19-20-21_counts.csv'`

```
real    66m42.834s
user    126m10.716s
sys     3m56.434s
ded1b425f7b5141336b8759dc8a3b5eb68075269  htseq_output/SRR10045016-17-18-19-20-21_counts.csv
```

Running with shell
`docker run --privileged --rm hs/ex2:latest /bin/bash -c 'time sh /root/workspace/ex2.sh && sha1sum /root/workspace/htseq_output/SRR10045016-17-18-19-20-21_counts.csv'`

```
real    48m49.509s
user    64m56.203s
sys     0m59.038s
ded1b425f7b5141336b8759dc8a3b5eb68075269  htseq_output/SRR10045016-17-18-19-20-21_counts.csv
```
