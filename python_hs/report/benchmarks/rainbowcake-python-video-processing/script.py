import os
import stat
import subprocess

ITERS = 100

image_name = "watermark.png"
video_name = "hi_chitanda_eru.mp4"

data_dir = "./data/rainbowcake-python-video-processing/"
output_dir = "./outputs/rainbowcake-python-video-processing/"

duration = 10

subprocess.run(["mkdir", "-p", output_dir], check=True)

# loop is our only logical addition
for i in range(ITERS):
    output_name = f"processed_hi_chitanda_eru_{i}.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-v",
            "quiet",
            "-stats",
            "-i",
            data_dir + video_name,
            "-i",
            data_dir + image_name,
            "-t",
            f"{duration}",
            "-filter_complex",
            "[0]trim=start_frame=0:end_frame=50[v0];\
        [0]trim=start_frame=100:end_frame=150[v1];[v0][v1]concat=n=2[v2];[1]hflip[v3];\
        [v2][v3]overlay=eof_action=repeat[v4];[v4]drawbox=50:50:120:120:red:t=5[v5]",
            "-map",
            "[v5]",
            output_dir + output_name,
        ],
        check=True,
    )

    print(f"{i}: Video {output_name} finished!")
