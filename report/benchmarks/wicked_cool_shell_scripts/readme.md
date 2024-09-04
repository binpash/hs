

docker run --rm -it --privileged $(docker build -q .) /bin/bash -c "window=8 sh run.sh && bash"
