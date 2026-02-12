# Rules for Secure & Optimized Docker Containerization

## 1. Multi-Stage Builds are Mandatory

**Rule:** Never ship build tools (gcc, git, poetry) to production. Use multi-stage builds to compile dependencies in a `builder` stage and copy only the artifacts (virtual environment or binary) to the final `runtime` stage.

* **Why:** Reduces image size (e.g., from 1GB to 200MB) and reduces the attack surface by removing potential exploit vectors.

```dockerfile
# Stage 1: Builder
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
# Copy only the installed packages from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

```

## 2. Run as Non-Root User (Strict Security)

**Rule:** The final active user in the container **must not be root**. You must explicitly create a user and switch to it.

* **Why:** If a container is compromised, a root user inside the container can potentially escape to the host kernel. This is a mandatory requirement for **ISO 27001** and **SOC2** audits.

```dockerfile
# Create a group and user with a specific UID (e.g., 1000)
RUN addgroup --system appgroup && adduser --system --group appuser

# Switch ownership of the application directory
COPY . /app
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER appuser

```

## 3. Explicit Layer Caching (The "Changes" Rule)

**Rule:** Order instructions from **least likely to change** to **most likely to change**.

1. System Install (`apt-get`)
2. Dependency Definition (`requirements.txt` / `pyproject.toml`)
3. Dependency Install (`pip install`)
4. Source Code Copy (`COPY . .`)

* **Why:** Docker caches layers. If you copy source code *before* installing requirements, every time you change a single line of code, Docker invalidates the cache and re-installs all Python packages, wasting 5+ minutes per build.

```dockerfile
# CORRECT
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . . 

# WRONG (Re-installs pip packages on every code change)
COPY . .
RUN pip install -r requirements.txt

```

## 4. Pin Base Images (Determinism)

**Rule:** Never use `:latest`. Pin to a specific version and OS variant. Ideally, pin the `SHA256` hash for banking-grade security.

* **Avoid:** `FROM python:latest`
* **Prefer:** `FROM python:3.11.8-slim-bookworm`
* **Banking Grade:** `FROM python@sha256:48d3...`

## 5. Handle Secrets & Env Vars

**Rule:** **NEVER** use `ENV` to store secrets (API Keys, Passwords) inside the Dockerfile. `ENV` values persist in the image history and can be read by anyone with the image.

* **Dev:** Use `.env` files.
* **Prod:** Inject secrets at runtime via Kubernetes Secrets or AWS Secrets Manager.

## 6. The `.dockerignore` Whitelist

**Rule:** Use a strict `.dockerignore` file. If you don't need it, don't context it.

* **Must Ignore:** `.git`, `__pycache__`, `.env`, `venv`, `node_modules`, `test_data`.

```text
# .dockerignore
**/.git
**/.DS_Store
**/__pycache__
**/*.pyc
.env
venv/
tests/
README.md

```

## 7. Entrypoint vs. CMD

**Rule:** Use `ENTRYPOINT` for the main executable and `CMD` for default arguments.

* **Exec Form:** Always use JSON array syntax `["executable", "param1"]`. The shell form `ENTRYPOINT command param1` breaks signal passing (CTRL+C won't kill the container).

```dockerfile
# ✅ CORRECT (Signals pass through)
ENTRYPOINT ["python", "-m", "uvicorn"]
CMD ["main:app", "--host", "0.0.0.0"]

```

## 8. Healthchecks

**Rule:** Define a `HEALTHCHECK` instruction so the orchestrator (Docker Swarm/K8s) knows if the app is actually alive, not just if the process is running.

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

```

---

### 🏆 The "Golden" Dockerfile Template

Use this template for your Python Agents.

```dockerfile
# syntax=docker/dockerfile:1

# 1. Base Image - Pinned & Slim
FROM python:3.11-slim-bookworm as builder

# 2. Environment Variables for Build
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# 3. Install System Deps (only if needed for compilation, e.g., gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 4. Install Python Deps (Cached Layer)
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# --- Final Stage ---
FROM python:3.11-slim-bookworm as runtime

WORKDIR /app

# 5. Create Non-Root User
RUN addgroup --system appgroup && adduser --system --group appuser

# 6. Copy only artifacts from Builder
COPY --from=builder /root/.local /root/.local
COPY --from=builder /usr/bin/curl /usr/bin/curl

# 7. Setup Path
ENV PATH=/root/.local/bin:$PATH

# 8. Copy Application Code
COPY --chown=appuser:appgroup . .

# 9. Security & Port
USER appuser
EXPOSE 8000

# 10. Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# 11. Entrypoint
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

```