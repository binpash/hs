#!/bin/bash

set -euo pipefail

readonly API_BASE="https://storage.googleapis.com/storage/v1/b/ugc-dataset/o?prefix=original_videos/&fields=items(name,size),nextPageToken"
readonly RES=1080

fetch_file_list() {
  local token=""
  
  while true; do
    local url="${API_BASE}${token:+&pageToken=$token}"
    local response
    response="$(curl -s "$url")"
    
    echo "$response" | jq -r ".items[] | select( .name | contains(\"${RES}P\") ) | [.size,.name] | @tsv"
    
    token="$(echo "$response" | jq -r '.nextPageToken // empty')"
    [[ -z $token ]] && break
  done
}

curl_conf() {
  awk -F$'\t' '{ print "url = https://storage.googleapis.com/ugc-dataset/"$2 }'
}

download_files() {
  curl -fLZ -C - --remote-name-all -K -
  touch .downloaded
}

download_watermark() {
  local REPO="IntelliSys-Lab/RainbowCake-ASPLOS24"
  local HASH="684aa457038ce49ff299ba11fea6876f83c924f8"
  local PATH_="applications/python_video_processing/src/watermark.png"
  curl -LO "https://raw.githubusercontent.com/$REPO/$HASH/$PATH_"
}

main() {
  cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
  cd ../../data/rainbowcake-python-video-processing/
  download_watermark
  fetch_file_list | curl_conf | download_files
}

main
