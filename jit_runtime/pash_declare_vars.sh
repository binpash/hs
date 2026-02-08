#!/bin/bash

vars_file="${1?File not given}"

# pash_redir_output echo "Writing vars to: $vars_file"

pash_redir_output echo "$$: [DECLARE_VARS] Saving variables - current IFS=$(declare -p IFS 2>&1 || echo 'unset'), PASH_OLD_IFS=$(declare -p PASH_OLD_IFS 2>&1 || echo 'unset')"
echo "cd \"${PWD}\"" > "$vars_file"
declare -p >> "$vars_file"
pash_redir_output echo "$$: [DECLARE_VARS] After declare -p to $vars_file"
declare -f >> "$vars_file"
trap >> "$vars_file"
echo "BASH_ARGV0=\"$0\"" >> "$vars_file"
echo '${hs_set_options_cmd}' >> "$vars_file"
echo 'set -- "${hs_runtime_tmp_args[@]}"' >> "$vars_file"
${RUNTIME_LIBRARY_DIR}/fd_util -s -f "$vars_file.fds"
