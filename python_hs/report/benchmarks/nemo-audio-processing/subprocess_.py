# Copyright (c) 2020, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# NOTE: The script has been factored into two for loops, rather than one.
# This is for the preprocessor's sake -- otherwise it spends a lot of time inlining
# all the audio metadata
import json
import logging
import os
import subprocess

data_root = "data/nemo-audio-processing"

all_entries = {}
for v in json.load(open(os.path.join(data_root, "to_process.json"))):
    # v: transcript_text, flac, wav, and manifest_file
    # Convert FLAC file to WAV
    subprocess.run(["mkdir", "-p", os.path.dirname(v[2])])
    subprocess.run(["sox", v[1], v[2]], check=True)
    duration = subprocess.run(
        f"soxi -D {v[2]}", check=True, shell=True, capture_output=True
    ).stdout
    entry = {}
    entry["audio_filepath"] = os.path.abspath(v[2])
    entry["duration"] = float(duration)
    entry["text"] = v[0]
    if v[3] not in all_entries:
        all_entries[v[3]] = []
    all_entries[v[3]].append(entry)

# Write all manifest files
for manifest_file, entries in all_entries.items():
    with open(manifest_file, "w") as fout:
        for m in entries:
            fout.write(json.dumps(m) + "\n")

logging.info("Done!")
