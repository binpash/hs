# hs/dgsh: the base image plus the libraries FFmpeg's configure needs. No
# input data: ./setup downloads the datasets and clones + builds FFmpeg onto
# the host (inside this image, so those libraries are present), and run_base
# mounts the result read-only at run time.
FROM hs

WORKDIR /srv/hs
RUN sed -i -e's/ main/ main contrib non-free/g' /etc/apt/sources.list.d/debian.sources
RUN apt update
RUN apt install -y unzip \
  yasm nasm cmake libx264-dev libx265-dev libvpx-dev libfdk-aac-dev \
  libopus-dev libass-dev libvpx-dev libfreetype6-dev libmp3lame-dev \
  libfdk-aac-dev libxvidcore-dev libvorbis-dev libtheora-dev libavcodec-dev \
  libavdevice-dev libavfilter-dev libavformat-dev libavutil-dev libswscale-dev \
  libswresample-dev \
  gawk
RUN mkdir -p report/benchmarks
COPY ./inner report/benchmarks/dgsh
