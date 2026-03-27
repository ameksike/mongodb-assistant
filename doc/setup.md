# Setup Guide

Simple and complete ways to start the project.

---

## Option A: Simple setup with make (recommended)

This is the fastest path.

```bash
make setup
make model:select modelName=phi-2
make dev
```

Verify:
- `http://localhost:8000/health`
- `http://localhost:8000/docs`

What `make setup` does:
- Creates `venv/`
- Installs dependencies inside `venv/`
- Creates `cfg/.env` from `cfg/.env.example` if missing

---

## Option B: Full manual setup without make

Use this path if you want full control.

### 1) Create virtual environment

```bash
python -m venv venv
```

### 2) Activate virtual environment

Windows (PowerShell):
```bash
.\venv\Scripts\Activate.ps1
```

Linux/macOS:
```bash
source venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Create local environment file

Windows (PowerShell):
```bash
copy cfg\.env.example cfg\.env
```

Linux/macOS:
```bash
cp cfg/.env.example cfg/.env
```

### 5) Download a local model

Catalog model (skips download if the file already exists; use `--force` to re-download):
```bash
python bin/download.py --model phi-2
```

List catalog and on-disk files:
```bash
python bin/download.py --list
```

Remove one catalog model file or clean `models/`:
```bash
python bin/download.py --remove phi-2
python bin/download.py --remove-file custom.gguf
python bin/download.py --clean
```

### 6) Start the API server

```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 7) Verify

- `http://localhost:8000/health`
- `http://localhost:8000/docs`

---

## Notes

- If you use Option A, you do not need to manually activate `venv` for project commands.
- If you use Option B, activate `venv` every new terminal session.
- `cfg/.env` controls providers and runtime settings (`LLM_PROVIDER`, `WORKFLOW_PROVIDER`, and model path).
