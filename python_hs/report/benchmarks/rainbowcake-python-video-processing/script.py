import glob
import subprocess
import os

data_dir = "./data/rainbowcake-python-video-processing/"
output_dir = "./output/rainbowcake-python-video-processing/"

image_path = os.path.join(data_dir, "watermark.png")

subprocess.run(["mkdir", "-p", output_dir], check=True)

for video_name in glob.glob(f"{data_dir}/*.mkv"):
    basename = os.path.basename(video_name)
    output_name = f"processed_{basename}"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "quiet",
            "-stats",
            "-i",
            video_name,
            "-i",
            image_path,
            "-filter_complex",
            "[1]hflip[v3];\
            [0][v3]overlay=eof_action=repeat[v4];\
            [v4]drawbox=50:50:120:120:red:t=5[v5]",
            "-map",
            "[v5]",
            output_dir + output_name,
        ],
        check=True,
    )

    print(f"Video {output_name} finished!")
