import subprocess

for _ in range(2):
    p1 = subprocess.Popen(['echo'], stdout=subprocess.PIPE)
    subprocess.run(['echo'], stdin=p1.stdout)
