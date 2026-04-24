# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.13-slim-bookworm

LABEL io.modelcontextprotocol.server.name="io.github.n24q02m/imagine-mcp"
LABEL org.opencontainers.image.source="https://github.com/n24q02m/imagine-mcp"
LABEL org.opencontainers.image.licenses="MIT"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -m appuser \
    && chown -R appuser:appuser /app
USER appuser

ENTRYPOINT ["python", "-m", "imagine_mcp"]
