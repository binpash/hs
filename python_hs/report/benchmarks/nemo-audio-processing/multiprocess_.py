import functools
import json
import logging
import multiprocessing
import os
import subprocess

data_root = "data/nemo-audio-processing"
num_workers = 16


def __process_transcript(v):
    subprocess.run(["mkdir", "-p", os.path.dirname(v[2])])
    subprocess.run(["sox", v[1], v[2]], check=True)
    duration = subprocess.run(
        f"soxi -D {v[2]}", check=True, shell=True, capture_output=True
    ).stdout
    return {
        "audio_filepath": os.path.abspath(v[2]),
        "duration": float(duration),
        "text": v[0],
        "manifest": v[3],
    }


files = json.load(open(os.path.join(data_root, "to_process.json")))
all_entries = {}

with multiprocessing.Pool(num_workers) as p:
    processing_func = functools.partial(__process_transcript)
    results = p.imap(processing_func, files)
    for result in results:
        if result["manifest"] not in all_entries:
            all_entries[result["manifest"]] = []
        all_entries[result["manifest"]].append(result)

for manifest_file, entries in all_entries.items():
    with open(manifest_file, "w") as fout:
        for m in entries:
            del m["manifest"]
            fout.write(json.dumps(m) + "\n")

logging.info("Done!")
