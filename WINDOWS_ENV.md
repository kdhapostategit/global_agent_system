# Windows stability (CrewAI / Chroma / native extensions)

## What causes `STATUS_ACCESS_VIOLATION` (0xC0000005 / 3221225477)?

On Windows this is almost always **native code** (not pure Python): mixed **NumPy ABI**, **ONNX Runtime** (pulled by **ChromaDB**), **LanceDB**, or **OpenMP** thread oversubscription across DLLs. CrewAI imports **chromadb** and **lancedb**; embedding paths can load **onnxruntime**.

This project pins **NumPy 1.26.x** (`numpy>=1.26.4,<2`) so all wheels link against a **single NumPy 1.x ABI**—mixing **NumPy 2** with extensions built for **NumPy 1** is a common source of hard crashes.

## Dependency alignment

| Area | Approach |
|------|----------|
| **NumPy** | Stay on **1.26.x** until all native deps officially support NumPy 2 on Windows. |
| **Gemini / embeddings** | Use **`google-genai`** via Crew’s **`google-vertex`** embedder (`gemini-embedding-*` models). Do **not** rely on the deprecated **`google-generativeai`** package for new code. |
| **Lockfile** | `uv.lock` is generated with `[tool.uv] required-environments` for **win_amd64** so **lancedb** resolves to a Windows wheel (0.30.0), not a Linux-only 0.30.1. |

## Recommended environment variables

Add these to `.env` (or system env) to reduce OpenMP / tokenizer thread fights that can destabilize native stacks:

```env
# Limit BLAS / OpenMP threads (often helps ONNX + NumPy stacks on Windows)
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
OPENBLAS_NUM_THREADS=1
NUMEXPR_NUM_THREADS=1

# Hugging Face tokenizers
TOKENIZERS_PARALLELISM=false

# Optional: ONNX Runtime diagnostics (only if debugging; can slow runs)
# ORT_LOG_SEVERITY_LEVEL=3
```

## Clean reinstall

From `global_agent_system/`:

```powershell
Remove-Item -Recurse -Force .venv -ErrorAction SilentlyContinue
uv sync
```

Ensure you only have **one** Python environment on `PATH` when running `kickoff` (no mixing `pip install` into a different interpreter than `uv run`).

## If crashes persist

1. Confirm **only one NumPy** is installed: `uv run python -c "import numpy; print(numpy.__version__, numpy.__file__)"`.
2. Temporarily set **`memory=False`** on `Crew` (if you enabled memory) to reduce Chroma activity—but **knowledge** may still initialize embeddings.
3. Try **Python 3.11** instead of 3.12 if you use bleeding-edge wheels (narrower test matrix on Windows).
4. As a last resort, switch embedder to **`openai`** or **`ollama`** (see CrewAI docs) to avoid Google embedding + Chroma default paths—but **test** your use case.

## Security note

Never commit `.env`. Rotate API keys if they were ever committed or pasted into chat logs.
