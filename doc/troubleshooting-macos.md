# Troubleshooting: macOS

Common issues when setting up the project on macOS and how to fix them.

---

## 1. `llama-cpp-python` fails to install (Xcode license / compiler not found)

### Symptom

```
error: command 'clang' failed
```

or

```
xcode-select: error: tool 'xcodebuild' requires Xcode, but active developer
directory is a command line tools instance
```

or the system prompts you to accept Apple's EULA and you cannot (e.g. corporate policy).

### Cause

`llama-cpp-python` compiles C++ code from source during `pip install`. On macOS this requires **Xcode Command Line Tools (CLT)**, which includes `clang`, `make`, and system headers. Apple requires accepting a license agreement before the tools can be used.

### Solutions (pick one)

#### A) Accept the Xcode CLT license (free, simplest)

```bash
xcode-select --install          # download and install CLT
sudo xcodebuild -license accept # accept the EULA from terminal
```

Then re-run `make setup` or `pip install -r requirements.txt`.

#### B) Use pre-built wheels (no compiler needed)

`llama-cpp-python` publishes pre-built wheels for macOS. Install them directly:

```bash
# CPU-only
pip install llama-cpp-python \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu

# Apple Silicon (M1/M2/M3/M4) with Metal GPU acceleration
pip install llama-cpp-python \
  --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/metal
```

> **Note:** a matching wheel must exist for your exact Python version and macOS architecture. If pip falls back to source build, try option A or C.

#### C) Use Homebrew GCC instead of Xcode (avoids Apple EULA)

```bash
brew install gcc cmake

CC=$(brew --prefix gcc)/bin/gcc-14 \
CXX=$(brew --prefix gcc)/bin/g++-14 \
pip install llama-cpp-python
```

This uses the GNU compiler from Homebrew, which has no Apple license dependency.

#### D) Skip local LLM entirely

If you don't need a local model, use a cloud-based provider. No compilation required:

```env
# In cfg/.env
LLM_PROVIDER=REMOTE    # LangChain + Gemini
# or
LLM_PROVIDER=VERTEXAI  # google-genai SDK (JSON-enforced)
```

See the [LLM Providers](README.md#llm-providers) section for authentication setup.

#### E) Use Ollama as an external LLM server

[Ollama](https://ollama.com) is a standalone LLM server that ships pre-compiled for macOS. No compiler toolchain needed:

```bash
brew install ollama
ollama pull mistral
ollama serve            # runs on http://localhost:11434
```

> **Note:** the project does not include an Ollama provider yet. This would require implementing a new `LlmOllamaService` using LangChain's `ChatOllama`.

---

## 2. SSL certificate error when downloading models

### Symptom

```
SSL: CERTIFICATE_VERIFY_FAILED
certificate verify failed: unable to get local issuer certificate
```

### Cause

Python installed from [python.org](https://python.org) on macOS ships its own OpenSSL and does not use the system certificate store. The bundled certificate file is often empty or outdated.

### Solution

This is already fixed in the project. The `ModelDownloadService` uses `certifi` as a certificate source. Make sure `certifi` is installed:

```bash
pip install certifi
```

If you still have issues after `make setup`, you can also run Apple's certificate installer:

```bash
# Replace 3.10 with your Python version
open "/Applications/Python 3.10/Install Certificates.command"
```

---

## 3. `python` command not found

### Symptom

```
make: python: No such file or directory
```

### Cause

macOS does not ship a `python` binary. The correct command is `python3`. Older macOS versions had `/usr/bin/python` pointing to Python 2, but Apple removed it.

### Solution

This is already fixed in the Makefile. It auto-detects `python3` on macOS/Linux:

```makefile
BASE_PYTHON := $(shell command -v python3 2>/dev/null || echo python)
```

If you still see this error, verify Python 3 is installed:

```bash
python3 --version
```

If not installed:

```bash
# Homebrew (recommended)
brew install python

# Or download from https://www.python.org/downloads/macos/
```

---

## 4. `cmake` not found

### Symptom

```
ERROR: CMake must be installed to build llama-cpp-python
```

### Solution

```bash
brew install cmake
```

Or use pre-built wheels (see section 1, option B) to skip compilation entirely.

---

## 5. Quick diagnostic

Run the pre-flight check to identify missing dependencies before setup:

```bash
make preflight
```

Expected output on a correctly configured macOS system:

```
  Conversational Assistance System v1.0.0
  ================================================

  [OK]   Python 3.12.3 (/opt/homebrew/bin/python3)
  [OK]   pip available (pip 24.0 from ...)
  [OK]   venv module available
  [OK]   C/C++ compiler available
  [OK]   cmake available
  [OK]   make available
  [OK]   git available
  [OK]   curl available
  [OK]   OS: macOS 14.4.1 (arm64)

  Results: 9 passed, 0 warnings, 0 failures
  Ready to run: make project:setup
```

Any `[FAIL]` or `[WARN]` items should be addressed before running `make setup`.
