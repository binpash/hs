#!/usr/bin/env python3

import fnmatch
import json
import logging
import os
import subprocess

data_root = "data/nemo-audio-processing"
dest_root = "output/nemo-audio-processing"

logging.basicConfig(level=logging.INFO)
# data_sets = [
# "dev_clean",
# "dev_other",
# "train_clean_100",
# "train_clean_360",
# "train_other_500",
# "test_clean",
# "test_other",
# ]

data_set = "train_clean_100"
MAX_DATA_SIZE = 5000
# TODO: Figure out how much data to use.
all_metadata = []
logging.info(f"\n\nWorking on: {data_set}")
filepath = os.path.join(data_root, data_set + ".tar.gz")
logging.info(f"Processing {data_set}")
data_folder = os.path.join(
    os.path.join(data_root, "LibriSpeech"),
    data_set.replace("_", "-"),
)
dst_folder = os.path.join(dest_root, data_set.replace("_", "-")) + "-processed"
manifest_file = os.path.join(data_root, data_set + ".json")
subprocess.run(["mkdir", "-p", dst_folder])
files = [
    os.path.join(v[0], filename)
    for v in os.walk(data_folder)
    for filename in fnmatch.filter(v[2], "*.trans.txt")
]
for file in files:
    transcript_root = os.path.dirname(file)
    with open(file) as f:
        for line in f:
            id, text = line[: line.index(" ")], line[line.index(" ") + 1 :]
            transcript_text = text.lower().strip()
            flac_file = os.path.join(transcript_root, id + ".flac")
            wav_file = os.path.join(dst_folder, id + ".wav")
            all_metadata.append((transcript_text, flac_file, wav_file, manifest_file))

    if len(all_metadata) > MAX_DATA_SIZE:
        break

with open(os.path.join(data_root, "to_process.json"), "w") as f:
    json.dump(all_metadata, f)
