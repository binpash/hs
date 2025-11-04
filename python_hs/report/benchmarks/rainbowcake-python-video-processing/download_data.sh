#!/bin/bash

BENCHMARK=rainbowcake-python-video-processing
DOWNLOAD_PATH=https://raw.githubusercontent.com/IntelliSys-Lab/RainbowCake-ASPLOS24/684aa457038ce49ff299ba11fea6876f83c924f8/applications/python_video_processing/src/

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
cd ../../ || exit

mkdir -p data/$BENCHMARK
cd data/$BENCHMARK

if [ ! -f watermark.png ]; then
  curl -LO "$DOWNLOAD_PATH/watermark.png"
fi

if [ ! -f hi_chitanda_eru.mp4 ]; then
  curl -LO "$DOWNLOAD_PATH/hi_chitanda_eru.mp4"
fi

