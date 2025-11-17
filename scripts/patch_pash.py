#!/usr/bin/env python3

from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
PASH_DIR = REPO_ROOT / "deps" / "pash"


def patch_env_vars():
    target = PASH_DIR / "python_pkgs" / "sh_expand" / "env_vars_util.py"
    if not target.exists():
        print(f"[patch_pash] Skipping env_vars patch, {target} does not exist.", file=sys.stderr)
        return

    text = target.read_text()
    updated = False

    decode_line = "            line = line[:-1].decode('utf-8', errors='replace')"
    if decode_line in text and ".strip()" not in text.split(decode_line, 1)[1].split("\n", 1)[0]:
        text = text.replace(
            decode_line,
            "            line = line[:-1].decode('utf-8', errors='replace').strip()",
            1,
        )
        updated = True

    guard_snippet = (
        '            # Skip empty lines or lines that don\'t start with "declare"\n'
        "            if not line or not line.startswith(\"declare\"):\n"
        "                continue\n"
        "            # Skip lines that don't have the expected format\n"
        "            parts = line.split(\" \", maxsplit=2)\n"
        "            if len(parts) < 3:\n"
        "                continue\n"
        "            _, var_type, rest = parts\n"
    )
    if guard_snippet not in text:
        original = '            _, var_type, rest = line.split(" ", maxsplit=2)\n'
        if original in text:
            text = text.replace(original, guard_snippet, 1)
            updated = True
        else:
            print("[patch_pash] Expected declare parsing snippet not found in env_vars_util.py", file=sys.stderr)

    if updated:
        target.write_text(text)
        print("[patch_pash] Patched env_vars_util.py")
    else:
        print("[patch_pash] env_vars_util.py already up to date")


def ensure_imports(content: str, module: str) -> str:
    if f"import {module}" in content:
        return content

    anchor = "import server_util"
    if anchor in content:
        return content.replace(anchor, f"{anchor}\nimport {module}", 1)
    # Fallback: append at top of file
    return f"import {module}\n{content}"


def insert_function(content: str, func_code: str) -> str:
    if "def get_bash_version_tuple():" in content:
        return content

    split_idx = content.find("\n\n", content.find("import "))
    if split_idx == -1:
        split_idx = len(content)
    return content[:split_idx + 2] + func_code + content[split_idx + 2 :]


def patch_compilation_server():
    target = PASH_DIR / "compiler" / "pash_compilation_server.py"
    if not target.exists():
        print(f"[patch_pash] Skipping compilation server patch, {target} does not exist.", file=sys.stderr)
        return

    text = target.read_text()
    original_text = text

    text = ensure_imports(text, "subprocess")
    text = ensure_imports(text, "re")

    func_code = (
        "def get_bash_version_tuple():\n"
        "    \"\"\"Get bash version as a tuple (major, minor, patch).\"\"\"\n"
        "    try:\n"
        "        result = subprocess.run(['bash', '--version'], capture_output=True, text=True, timeout=5)\n"
        "        version_line = result.stdout.split('\\n')[0]\n"
        "        match = re.search(r'(\\d+)\\.(\\d+)\\.(\\d+)', version_line)\n"
        "        if match:\n"
        "            return tuple(map(int, match.groups()))\n"
        "    except Exception:\n"
        "        pass\n"
        "    return (5, 1, 0)\n\n"
    )
    text = insert_function(text, func_code)

    call_snippet = "        vars_dict = env_vars_util.read_vars_file(var_file)\n"
    replacement = (
        "        bash_version_tuple = get_bash_version_tuple()\n"
        "        vars_dict = env_vars_util.read_vars_file(var_file, bash_version_tuple)\n"
    )
    if call_snippet in text and replacement not in text:
        text = text.replace(call_snippet, replacement, 1)

    if text != original_text:
        target.write_text(text)
        print("[patch_pash] Patched pash_compilation_server.py")
    else:
        print("[patch_pash] pash_compilation_server.py already up to date")


def patch_compiler():
    target = PASH_DIR / "compiler" / "pash_compiler.py"
    if not target.exists():
        print(f"[patch_pash] Skipping pash_compiler patch, {target} does not exist.", file=sys.stderr)
        return

    text = target.read_text()
    original_text = text

    text = ensure_imports(text, "subprocess")
    text = ensure_imports(text, "re")

    func_code = (
        "def get_bash_version_tuple():\n"
        "    \"\"\"Get bash version as a tuple (major, minor, patch).\"\"\"\n"
        "    try:\n"
        "        result = subprocess.run(['bash', '--version'], capture_output=True, text=True, timeout=5)\n"
        "        version_line = result.stdout.split('\\n')[0]\n"
        "        match = re.search(r'(\\d+)\\.(\\d+)\\.(\\d+)', version_line)\n"
        "        if match:\n"
        "            return tuple(map(int, match.groups()))\n"
        "    except Exception:\n"
        "        pass\n"
        "    return (5, 1, 0)\n\n"
    )
    text = insert_function(text, func_code)

    call_snippet = "    vars_dict = env_vars_util.read_vars_file(args.var_file)\n"
    replacement = (
        "    bash_version_tuple = get_bash_version_tuple()\n"
        "    vars_dict = env_vars_util.read_vars_file(args.var_file, bash_version_tuple)\n"
    )
    if call_snippet in text and replacement not in text:
        text = text.replace(call_snippet, replacement, 1)

    if text != original_text:
        target.write_text(text)
        print("[patch_pash] Patched pash_compiler.py")
    else:
        print("[patch_pash] pash_compiler.py already up to date")


def main():
    if not PASH_DIR.exists():
        print(f"[patch_pash] {PASH_DIR} not found. Skipping PaSh patch.", file=sys.stderr)
        sys.exit(0)

    patch_env_vars()
    patch_compilation_server()
    patch_compiler()


if __name__ == "__main__":
    main()
