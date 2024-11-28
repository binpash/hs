#! /bin/sh
generate_unique_file() {
    local dir="$OUTPUT_DIR"
    local prefix="strace_log"
    local counter_file="$dir/${prefix}"
    if [ ! -f "$counter_file" ]; then
        echo 0 > "$counter_file"
    fi
    local counter
    counter=$(<"$counter_file")
    counter=$((counter + 1))
    echo "$counter" > "$counter_file"
    local filename="$dir/${prefix}_${counter}"
    echo "$filename"
}

OUTPUT=${OUTPUT:-.}
SCRIPTS=${SCRIPTS:-./scripts}
touch "$OUTPUT"/giant
logfile=$(generate_unique_file)
strace -y -f  --seccomp-bpf --trace=fork,clone,%file -o $logfile env -i bash -c python3 "$SCRIPTS"/giant_file.py "$OUTPUT"/giant 100
$PARSE $logfile > $(generate_unique_file)
