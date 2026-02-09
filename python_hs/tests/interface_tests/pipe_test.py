import subprocess

base64 = ["base64", "/bin/sh"]
head_base64 = ["head", "-n", "5"]

out1 = subprocess.Popen(base64, stdout=subprocess.PIPE)
subprocess.run(head_base64, stdin=out1.stdout)
subprocess.run(["echo", "Run 1"])
