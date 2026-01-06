import glob
import subprocess
import os
import json

input_dir = "data/nemo-audio-processing/"
output_dir = "output/nemo-audio-processing/"

subprocess.run(["mkdir", "-p", output_dir], check=True)

results = []

for flac_path in glob.glob(os.path.join(input_dir, "**/*.flac"), recursive=True):
    wav_path = os.path.join(
        output_dir, os.path.splitext(os.path.basename(flac_path))[0] + ".wav"
    )
    subprocess.run(["sox", flac_path, wav_path], check=True)
    duration = subprocess.run(
        ["soxi", "-D", wav_path], check=True, capture_output=True, text=True
    ).stdout
    results.append({
        "audio_filepath": os.path.abspath(wav_path),
        "duration": float(duration),
    })


with open(os.path.join(output_dir, "mainfest.json"), "w") as f:
    json.dump(results, f)
