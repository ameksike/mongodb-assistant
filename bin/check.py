"""Pre-flight check: verify Python version, tools, and project files.

Compatible with Windows, macOS, and Linux. Uses only ASCII output to avoid
encoding issues on legacy Windows terminals (cp1252 / cp437).
"""

import pathlib
import platform
import shutil
import subprocess
import sys

PROJECT_NAME = "Conversational Assistance System"
PROJECT_VERSION = "1.0.0"
MIN_PYTHON = (3, 10)

_ok = 0
_warn = 0
_fail = 0


def passed(msg: str) -> None:
    global _ok
    _ok += 1
    print(f"  [OK]   {msg}")


def warning(msg: str) -> None:
    global _warn
    _warn += 1
    print(f"  [WARN] {msg}")


def failed(msg: str) -> None:
    global _fail
    _fail += 1
    print(f"  [FAIL] {msg}")


def _check_python() -> None:
    v = sys.version_info
    py_ver = f"{v.major}.{v.minor}.{v.micro}"
    if (v.major, v.minor) >= MIN_PYTHON:
        passed(f"Python {py_ver} ({sys.executable})")
    else:
        failed(
            f"Python {py_ver} found but >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]} required"
        )


def _check_tool(
    name: str, alt: str = "", required: bool = False, hint: str = ""
) -> None:
    found = shutil.which(name) or (shutil.which(alt) if alt else None)
    label = hint or name
    if found:
        passed(f"{name} available")
    elif required:
        failed(f"{name} not found -- {label}")
    else:
        warning(f"{name} not found -- {label}")


def _check_module(name: str, hint: str = "") -> None:
    try:
        __import__(name)
        passed(f"{name} module available")
    except ImportError:
        failed(f"{name} module missing -- {hint}")


def _check_compiler() -> None:
    """C/C++ compiler is needed to build llama-cpp-python from source."""
    os_name = platform.system()
    if os_name == "Windows":
        found = shutil.which("cl") or shutil.which("gcc") or shutil.which("cc")
        hint = "install Visual Studio Build Tools or MinGW"
    elif os_name == "Darwin":
        found = shutil.which("clang") or shutil.which("gcc")
        hint = "run: xcode-select --install"
    else:
        found = shutil.which("gcc") or shutil.which("cc") or shutil.which("clang")
        hint = "install build-essential (apt) or gcc (yum/dnf)"

    if found:
        passed("C/C++ compiler available")
    else:
        warning(f"C/C++ compiler not found -- {hint} (needed for llama-cpp-python)")


def _check_cmake() -> None:
    if shutil.which("cmake"):
        passed("cmake available")
    else:
        warning("cmake not found -- needed to build llama-cpp-python")


def _check_pip() -> None:
    """Verify pip is available and belongs to the same Python running this script."""
    pip_bin = shutil.which("pip") or shutil.which("pip3")
    if not pip_bin:
        failed("pip not found -- install python3-pip or ensurepip")
        return

    try:
        out = subprocess.check_output(
            [sys.executable, "-m", "pip", "--version"],
            stderr=subprocess.DEVNULL,
            text=True,
        )
        passed(f"pip available ({out.strip().split(',')[0]})")
    except Exception:
        passed("pip available")


def _check_file(
    path: str, on_missing: str = "", is_required: bool = True
) -> None:
    if pathlib.Path(path).exists():
        passed(f"{path} exists")
    elif is_required:
        failed(f"{path} missing -- {on_missing}")
    else:
        warning(f"{path} not found -- run: {on_missing}")


def _check_models() -> None:
    models = pathlib.Path("models")
    if not models.exists():
        warning("models/ directory not found -- run: make model:download")
        return
    gguf = sorted(
        p
        for p in models.iterdir()
        if p.is_file() and p.suffix.lower() in (".gguf", ".bin")
    )
    if gguf:
        for m in gguf:
            size_mb = m.stat().st_size // (1024 * 1024)
            passed(f"model: {m.name} ({size_mb} MB)")
    else:
        warning(
            "models/ exists but no .gguf/.bin files -- run: make model:download"
        )


def _os_display() -> str:
    os_name = platform.system()
    release = platform.release()
    arch = platform.machine()

    if os_name == "Darwin":
        try:
            mac_ver = platform.mac_ver()[0]
            if mac_ver:
                return f"macOS {mac_ver} ({arch})"
        except Exception:
            pass
        return f"macOS / Darwin {release} ({arch})"

    if os_name == "Linux":
        try:
            import distro  # type: ignore[import-untyped]

            name = distro.name(pretty=True)
            if name:
                return f"{name} ({arch})"
        except ImportError:
            pass
        return f"Linux {release} ({arch})"

    return f"{os_name} {release} ({arch})"


def main() -> None:
    print()
    print(f"  {PROJECT_NAME} v{PROJECT_VERSION}")
    print("  " + "=" * 48)
    print()

    _check_python()
    _check_pip()
    _check_module("venv", hint="install python3-venv")
    _check_compiler()
    _check_cmake()
    _check_tool("make", hint="you are running it, so this is unlikely")
    _check_tool("git", hint="optional but recommended")
    _check_tool("curl", hint="needed for run:health and workflow:list")
    _check_tool("docker", hint="needed only for containerised deployment")

    print()
    _check_file("cfg/.env.example", on_missing="project files incomplete")
    _check_file("cfg/.env", on_missing="make project:setup", is_required=False)
    _check_file("requirements.txt", on_missing="project files incomplete")
    _check_file("venv", on_missing="make project:setup", is_required=False)

    print()
    _check_models()

    print()
    passed(f"OS: {_os_display()}")

    print()
    print(f"  Results: {_ok} passed, {_warn} warnings, {_fail} failures")
    if _fail > 0:
        print("  Fix failures above before running: make project:setup")
    else:
        print("  Ready to run: make project:setup")
    print()

    sys.exit(1 if _fail > 0 else 0)


if __name__ == "__main__":
    main()
