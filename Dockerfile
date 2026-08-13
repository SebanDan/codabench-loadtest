FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

RUN --mount=type=cache,target=/root/.cache/uv \
    uv run playwright install-deps chromium && \
    uv run playwright install chromium

COPY . .

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

EXPOSE 8089 5557 5558

ENTRYPOINT ["uv", "run"]
CMD ["locust"]
