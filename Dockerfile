# ============================================================================
# Conversational Assistance System — Optimized LOCAL LLM Dockerfile
# ============================================================================
# Multi-stage build: compiles llama-cpp-python (C++) in a heavy builder stage,
# then copies only the finished virtualenv into a minimal runtime image.
#
# Build:
#   docker build -t mongodb-assistant .
#
# Run (mount model + env):
#   docker run -p 3333:3333 \
#     -v ./models:/app/models:ro \
#     -v ./cfg/.env:/app/cfg/.env:ro \
#     mongodb-assistant
#
# Override model at runtime:
#   docker run -p 3333:3333 \
#     -v ./models:/app/models:ro \
#     -e LLM_LOCAL_MODEL_PATH=models/phi-2.Q4_K_M.gguf \
#     mongodb-assistant
# ============================================================================


# --------------- Stage 1: builder -------------------------------------------
FROM python:3.10-slim AS builder

# llama-cpp-python compiles C++; pass CMAKE_ARGS for custom flags
# e.g. --build-arg CMAKE_ARGS="-DGGML_AVX2=ON" for AVX2 SIMD
ARG CMAKE_ARGS=""

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        cmake \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /build

COPY requirements.txt .

RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel \
 && CMAKE_ARGS="${CMAKE_ARGS}" \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt


# --------------- Stage 2: runtime -------------------------------------------
FROM python:3.10-slim

# Shared libs required by llama-cpp at runtime (libgomp for OpenMP threading)
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*

RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

WORKDIR /app

# Virtualenv from builder (only artifact carried over)
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Application source + default workflow definitions
COPY src/ src/
COPY cfg/workflows/ cfg/workflows/
COPY cfg/.env.example cfg/.env

# ---------- Default configuration (LOCAL LLM) ----------
ENV LLM_PROVIDER=LOCAL \
    LLM_PROMPT_FORMAT=text \
    LLM_LOCAL_MODEL_PATH=models/mistral-7b-instruct-v0.2.Q4_K_M.gguf \
    LLM_LOCAL_MODEL_N_CTX=4096 \
    LLM_LOCAL_MODEL_N_THREADS=4 \
    LLM_LOCAL_MODEL_TEMPERATURE=0.7 \
    WORKFLOW_PROVIDER=JSON \
    WORKFLOW_DIR=cfg/workflows

# Model directory — mount at runtime, never bake into the image
VOLUME ["/app/models"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3333/health')"

EXPOSE 3333

USER app

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "3333"]
