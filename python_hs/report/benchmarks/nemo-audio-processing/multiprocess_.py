import multiprocessing
import os
import subprocess
import json
import glob

num_workers = 16
input_dir = "data/nemo-audio-processing/"
output_dir = "output/nemo-audio-processing/"


paths = (
    (
        flac_path,
        os.path.join(
            output_dir, os.path.splitext(os.path.basename(flac_path))[0] + ".wav"
        ),
    )
    for flac_path in glob.glob(os.path.join(input_dir, "**/*.flac"), recursive=True)
)

subprocess.run(["mkdir", "-p", output_dir], check=True)


def __process_transcript(paths):
    flac_path, wav_path = paths
    subprocess.run(["sox", flac_path, wav_path], check=True)
    duration = subprocess.run(
        ["soxi", "-D", wav_path],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    return {
        "audio_filepath": os.path.abspath(wav_path),
        "duration": float(duration),
    }


results = []

with multiprocessing.Pool(num_workers) as p:
    results.extend(p.map(__process_transcript, paths))

with open(os.path.join(output_dir, "mainfest.json"), "w") as f:
    json.dump(results, f)
