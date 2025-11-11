import glob
import subprocess
import os

data_dir = "./data/rainbowcake-python-video-processing/"
output_dir = "./output/rainbowcake-python-video-processing/"

image_path = os.path.join(data_dir, "watermark.png")

duration = 10

subprocess.run(["mkdir", "-p", output_dir], check=True)

# loop is our only logical addition
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

    print(f"Video {output_name} finished!")
