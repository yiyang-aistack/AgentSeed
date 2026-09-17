# AgentSeed backend — LangGraph API server (in-memory runtime) served by uvicorn.
#
# Config is read from environment variables (see .env.example); no .env file is
# baked into the image, so secrets are only ever supplied at run time.
#
# Build:  docker build -t agentseed .
# Run:    docker run --rm -p 2026:2026 agentseed
#         (or `docker compose up` — see docker-compose.yml for the full defaults)

# ---- deps: resolve the uv-managed environment from the lockfile -------------
FROM python:3.12-slim AS deps
WORKDIR /app

# Copy only the manifest + lockfile first so this layer is cached and source
# edits do not re-run the (slow) `uv sync`.
# `--locked` (not `--frozen`): the build must fail when uv.lock no longer satisfies
# pyproject.toml, instead of quietly installing the locked-but-outdated versions.
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv \
    && uv sync --locked --no-dev

# ---- runtime: slim image with the resolved environment + source -------------
FROM python:3.12-slim AS runtime
WORKDIR /app

# Reuse the venv built in the deps stage; no uv / pip / build tooling ends up in
# the final image.
COPY --from=deps /app/.venv /app/.venv
ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

# HOST=0.0.0.0 so the published port is reachable from outside the container.
# PORT is required by backend/main.py (it fails fast, by design, when unset).
ENV HOST=0.0.0.0 \
    PORT=2026

# Application source + business-level graph registry. .dockerignore keeps .env,
# .venv, frontend/node_modules, logs, etc. out of the build context.
COPY backend ./backend
COPY agentConfig.yaml ./

EXPOSE 2026

CMD ["python", "backend/main.py"]
