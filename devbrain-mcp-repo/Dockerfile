# Imagem do DevBrain MCP para o Google Cloud Run.
# Build em duas etapas: uv resolve o ambiente a partir do uv.lock; a imagem final
# carrega apenas o .venv e roda como usuário sem privilégios.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0
WORKDIR /app

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project
COPY src ./src
RUN uv sync --locked --no-dev --no-editable

FROM python:3.12-slim-bookworm
RUN useradd --create-home --uid 10001 devbrain
COPY --from=builder --chown=devbrain:devbrain /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PORT=8080
USER devbrain
EXPOSE 8080
CMD ["devbrain-mcp-cloudrun"]
