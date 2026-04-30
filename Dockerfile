# syntax=docker/dockerfile:1
# Multi-target Dockerfile per spec
# `~/projects/.superpower/mcp-core/specs/2026-04-30-multi-mode-stdio-http-architecture.md`
# section D6. Build stdio: `docker buildx build --target stdio -t <repo>:stdio .`
# Build http:  `docker buildx build --target http  -t <repo>:http .`
# Build latest (= http): `docker buildx build --target http -t <repo>:latest .`

# ========================
# Stage 1: Builder
# ========================
FROM python:3.13-slim-bookworm AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN sed -i '/^\[tool\.uv\.sources\]/,/^$/d' pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

COPY . /app
RUN sed -i '/^\[tool\.uv\.sources\]/,/^$/d' pyproject.toml
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# ========================
# Stage 2: Runtime base (shared by stdio + http targets)
# ========================
FROM python:3.13-slim-bookworm AS runtime

LABEL io.modelcontextprotocol.server.name="io.github.n24q02m/imagine-mcp"
LABEL org.opencontainers.image.source="https://github.com/n24q02m/imagine-mcp"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/src /app/src

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser \
    && chown -R appuser:appuser /app
USER appuser

# ========================
# Stage 3a: stdio target (default for plugin marketplace & uvx-style usage)
# ========================
FROM runtime AS stdio
ENV MCP_TRANSPORT=stdio
ENTRYPOINT ["python", "-m", "imagine_mcp"]

# ========================
# Stage 3b: http target (multi-user remote daemon)
# ========================
FROM runtime AS http
ENV MCP_TRANSPORT=http \
    MCP_PORT=8080
EXPOSE 8080
ENTRYPOINT ["python", "-m", "imagine_mcp"]
