from python_hs import run

# TODO: Quote
random_sh = "base64 /dev/random | head -n 100000 > /dev/null"

run(["echo 'Run 1'"], _speculated=False)
run(random_sh)
run(["echo 'Run 2'"])
run(random_sh)
