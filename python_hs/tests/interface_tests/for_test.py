import subprocess

for i in range(3):
    subprocess.run(["echo", str(i)])
