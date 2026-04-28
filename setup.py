from __future__ import annotations

import fnmatch
import os
import shutil
import subprocess
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py as _build_py

try:
    from setuptools.command.bdist_wheel import bdist_wheel as _bdist_wheel
except Exception:  # pragma: no cover - fallback for older build environments
    try:
        from wheel.bdist_wheel import bdist_wheel as _bdist_wheel
    except Exception:
        _bdist_wheel = None


ROOT = Path(__file__).parent.resolve()
RUNTIME_ITEMS = [
    "hs",
    "pash-spec.sh",
    "requirements.txt",
    "scheduler",
    "preprocessor",
    "executor",
    "jit_runtime",
    "test",
]
TRY_RUNTIME_FILES = [
    "try",
    "LICENSE",
    "README.md",
    "STYLE.md",
]

IGNORE_NAMES = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".DS_Store",
    ".venv",
    "python_pkgs",
    "output_bash",
    "output_orch",
    "results",
}
IGNORE_PATTERNS = [
    "*.pyc",
    "*.pyo",
    "*.o",
    "*.so",
    "*.dylib",
    "*.egg-info",
    "fd_util",
    "set-diff",
    "try-commit",
    "try-summary",
]


def ignore_runtime_files(directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        if name in IGNORE_NAMES:
            ignored.add(name)
            continue
        if any(fnmatch.fnmatch(name, pattern) for pattern in IGNORE_PATTERNS):
            ignored.add(name)
    return ignored


class build_py(_build_py):
    def run(self) -> None:
        super().run()
        runtime_dst = Path(self.build_lib) / "binpash_hs" / "runtime"
        if runtime_dst.exists():
            shutil.rmtree(runtime_dst)
        runtime_dst.mkdir(parents=True)

        for item in RUNTIME_ITEMS:
            src = ROOT / item
            dst = runtime_dst / item
            if src.is_dir():
                shutil.copytree(src, dst, ignore=ignore_runtime_files)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        self._copy_try_runtime(runtime_dst)

        self._chmod_runtime_scripts(runtime_dst)
        self._build_native_helpers(runtime_dst)

    def _copy_try_runtime(self, runtime: Path) -> None:
        try_src = ROOT / "deps" / "try"
        if not (try_src / "try").exists() or not (try_src / "utils").is_dir():
            raise RuntimeError(
                "The deps/try submodule is missing. Run "
                "`git submodule update --init --recursive deps/try` and retry."
            )

        try_dst = runtime / "deps" / "try"
        try_dst.mkdir(parents=True)

        for relpath in TRY_RUNTIME_FILES:
            src = try_src / relpath
            if src.exists():
                dst = try_dst / relpath
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        shutil.copytree(
            try_src / "utils",
            try_dst / "utils",
            ignore=ignore_runtime_files,
        )

    def _chmod_runtime_scripts(self, runtime: Path) -> None:
        for relpath in [
            "hs",
            "pash-spec.sh",
            "deps/try/try",
            "test/test_orch.sh",
        ]:
            path = runtime / relpath
            if path.exists():
                path.chmod(path.stat().st_mode | 0o755)

    def _build_native_helpers(self, runtime: Path) -> None:
        if os.name != "posix" or not sys_platform_is_linux():
            raise RuntimeError("binpash-hs currently supports Linux builds only")

        self._require_build_tools()

        commands = [
            (["make"], runtime / "executor"),
            (["make", "-C", "utils"], runtime / "deps/try"),
        ]
        for command, cwd in commands:
            try:
                subprocess.run(command, cwd=cwd, check=True)
            except FileNotFoundError as exc:
                raise RuntimeError(
                    "Failed to build binpash-hs native helpers: `make` was not found. "
                    "Install build-essential or an equivalent Linux build toolchain."
                ) from exc
            except subprocess.CalledProcessError as exc:
                raise RuntimeError(
                    "Failed to build binpash-hs native helpers. On Ubuntu, install "
                    "build-essential libtool libtool-bin autoconf automake m4 "
                    "pkg-config python3.12-dev, plus the hS runtime prerequisites, "
                    "then retry."
                ) from exc

        for object_file in (runtime / "deps/try/utils").glob("*.o"):
            object_file.unlink()

    def _require_build_tools(self) -> None:
        missing = [
            tool
            for tool in ["make", "gcc", "libtoolize", "m4", "autoconf", "automake"]
            if shutil.which(tool) is None
        ]
        if missing:
            raise RuntimeError(
                "Missing native build tools required by binpash-hs/libdash: "
                f"{', '.join(missing)}. On Ubuntu, install them with "
                "`sudo apt-get install -y build-essential libtool libtool-bin "
                "autoconf automake m4 pkg-config python3.12-dev`."
            )


def sys_platform_is_linux() -> bool:
    return os.uname().sysname == "Linux"


cmdclass = {"build_py": build_py}

if _bdist_wheel is not None:

    class bdist_wheel(_bdist_wheel):
        def finalize_options(self) -> None:
            super().finalize_options()
            self.root_is_pure = False

        def get_tag(self) -> tuple[str, str, str]:
            _, _, platform_tag = super().get_tag()
            return "py3", "none", platform_tag

    cmdclass["bdist_wheel"] = bdist_wheel


setup(cmdclass=cmdclass)
