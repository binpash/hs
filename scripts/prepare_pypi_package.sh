#!/usr/bin/env bash
set -euo pipefail

usage() {
    cat <<'EOF'
Usage: scripts/prepare_pypi_package.sh [OPTIONS]

Build and check the binpash-hs package artifacts without publishing them.

Options:
  --set-version VERSION  Update pyproject.toml to VERSION before building.
  --install-tool          Reinstall the built wheel with `uv tool install --force`.
  --install-sudo-wrapper  Add /usr/local/bin wrappers for hs and binpash-hs-test.
                          This requires sudo and is useful because sudo often
                          ignores the user's ~/.local/bin PATH entry.
  --smoke                 After --install-tool, run hs --help and sudo hs -c.
  -h, --help              Show this help.

The script deliberately does not publish. The generated Linux wheel is useful
for local uv-tool testing, but PyPI rejects raw linux_x86_64 wheels. Publish the
sdist unless/until we add auditwheel-produced manylinux wheels.
EOF
}

install_tool=0
install_sudo_wrapper=0
run_smoke=0
set_version=""

while [ "$#" -gt 0 ]; do
    case "$1" in
        --set-version)
            if [ "$#" -lt 2 ]; then
                echo "Error: --set-version requires a version argument." >&2
                exit 2
            fi
            set_version="$2"
            shift
            ;;
        --install-tool)
            install_tool=1
            ;;
        --install-sudo-wrapper)
            install_sudo_wrapper=1
            ;;
        --smoke)
            install_tool=1
            run_smoke=1
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1" >&2
            usage >&2
            exit 2
            ;;
    esac
    shift
done

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv was not found on PATH." >&2
    echo "Install uv first, then rerun this script." >&2
    exit 1
fi

repo_root=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$repo_root"

echo "==> Preparing binpash-hs package from $repo_root"

if [ -n "$set_version" ]; then
    case "$set_version" in
        *[!0-9A-Za-z.!+_-]*|"")
            echo "Error: suspicious version string: $set_version" >&2
            exit 2
            ;;
    esac
    echo "==> Setting package version to $set_version"
    python3 - "$set_version" <<'PY'
from pathlib import Path
import re
import sys

version = sys.argv[1]
path = Path("pyproject.toml")
text = path.read_text()
new_text, count = re.subn(
    r'(?m)^version = "[^"]+"$',
    f'version = "{version}"',
    text,
    count=1,
)
if count != 1:
    raise SystemExit("Could not find exactly one project version in pyproject.toml")
path.write_text(new_text)
PY
fi

if [ ! -d deps/try/utils ]; then
    echo "==> Initializing deps/try submodule"
    git submodule update --init --recursive deps/try
elif [ ! -f deps/try/try ]; then
    echo "==> Refreshing deps/try submodule"
    git submodule update --init --recursive deps/try
fi

echo "==> Cleaning generated packaging directories"
rm -rf build binpash_hs.egg-info dist

echo "==> Building sdist and Linux wheel"
uv build

echo "==> Checking package metadata"
uvx twine check dist/*

echo "==> Checking archives for excluded local/artifact payloads"
sdist=$(find dist -maxdepth 1 -name 'binpash_hs-*.tar.gz' -print -quit)
wheel=$(find dist -maxdepth 1 -name 'binpash_hs-*.whl' -print -quit)

if [ -z "$sdist" ] || [ -z "$wheel" ]; then
    echo "Error: expected both an sdist and a wheel in dist/." >&2
    exit 1
fi

common_forbidden_pattern='paper-hs|artifact/|python_pkgs|report/output|report/resources|deps/try/(\.git$|\.github|docs|test|completions|man|scripts|Vagrantfile)|\.o$'
sdist_forbidden_pattern="${common_forbidden_pattern}|/(fd_util|set-diff|try-commit|try-summary)$"
wheel_forbidden_pattern="$common_forbidden_pattern"

if tar -tzf "$sdist" | grep -E "$sdist_forbidden_pattern"; then
    echo "Error: sdist contains files that should not be published." >&2
    exit 1
fi

if unzip -l "$wheel" | grep -E "$wheel_forbidden_pattern"; then
    echo "Error: wheel contains files that should not be published." >&2
    exit 1
fi

rm -rf build binpash_hs.egg-info

echo "==> Package artifacts are ready"
ls -lh dist/*
echo
echo "Publishable artifact for PyPI/TestPyPI: $sdist"
echo "Local-only test wheel: $wheel"

if [ "$install_tool" -eq 1 ]; then
    echo "==> Installing built wheel as a uv tool"
    uv tool install --force "$wheel"
fi

if [ "$install_sudo_wrapper" -eq 1 ]; then
    if ! command -v hs >/dev/null 2>&1; then
        echo "Error: hs is not on PATH. Use --install-tool first." >&2
        exit 1
    fi
    if ! command -v binpash-hs-test >/dev/null 2>&1; then
        echo "Error: binpash-hs-test is not on PATH. Use --install-tool first." >&2
        exit 1
    fi
    echo "==> Installing root-visible command wrappers"
    sudo ln -sf "$(command -v hs)" /usr/local/bin/hs
    sudo ln -sf "$(command -v binpash-hs-test)" /usr/local/bin/binpash-hs-test
fi

if [ "$run_smoke" -eq 1 ]; then
    echo "==> Running smoke checks"
    hs --help >/dev/null
    if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
        sudo -n "$(command -v hs)" -c 'echo hello'
    else
        echo "Skipping sudo smoke check because passwordless sudo is unavailable."
        echo "Run manually: sudo \"$(command -v hs)\" -c 'echo hello'"
    fi
fi

cat <<EOF

Next publish commands, after inspection:

  uv publish --publish-url https://test.pypi.org/legacy/ \\
    --check-url https://test.pypi.org/simple/ \\
    --token "\$TEST_PYPI_TOKEN" \\
    "$sdist"

  uv publish --token "\$PYPI_TOKEN" "$sdist"

Test the TestPyPI release with Python 3.12+ explicitly:

  python3.12 -m venv /tmp/binpash-hs-testpypi
  . /tmp/binpash-hs-testpypi/bin/activate
  python -m pip install --upgrade pip
  python -m pip install \\
    --index-url https://test.pypi.org/simple/ \\
    --extra-index-url https://pypi.org/simple/ \\
    binpash-hs
EOF
