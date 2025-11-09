#!/bin/bash

BENCHMARK=rainbowcake-python-video-processing
DOWNLOAD_PATH=https://raw.githubusercontent.com/IntelliSys-Lab/RainbowCake-ASPLOS24/684aa457038ce49ff299ba11fea6876f83c924f8/applications/python_video_processing/src/

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
cd ../../ || exit

mkdir -p data/$BENCHMARK
cd data/$BENCHMARK

curl -kLO https://www.crcv.ucf.edu/data/UCF11_updated_mpg.rar

unrar -f UCF11_updated_mpg.rar
rm UCF11_updated_mpg.rar
find UCF11_updated_mpg/ -type f -path 'UCF11_*.mpg' -exec mv {} . \;

touch .downloaded

