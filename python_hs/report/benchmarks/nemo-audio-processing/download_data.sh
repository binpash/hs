#!/usr/bin/env python3

from datasets import load_dataset
import soundfile as sf

ds = load_dataset("MLCommons/speech-wikimedia", split="train", streaming=True)

long_files = []

for i, example in enumerate(ds):
    # example["audio"]["path"] points to the local FLAC after download
    path = example["audio"]["path"]
    data, sr = sf.read(path)   # 16 kHz mono
    duration_min = len(data) / sr / 60.0
    if duration_min >= 45:
        long_files.append((path, duration_min))
        if len(long_files) >= 20:
            break

print(long_files)
