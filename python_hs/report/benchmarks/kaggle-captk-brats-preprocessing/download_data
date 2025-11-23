#!/usr/bin/env bash

set -eu

COMPETITION="rsna-miccai-brain-tumor-radiogenomic-classification"

# to top directory of this script
cd -- "$(dirname -- "${BASH_SOURCE[0]}")" || exit
# to the report directory
cd ../../ || exit

data_dir="$(readlink -f "data/kaggle-captk-brats-preprocessing")"

mkdir -p "$data_dir"
cd "$data_dir" || exit

kaggle competitions download -c "$COMPETITION"
touch .downloaded
unzip -q '*.zip'

# install captk
