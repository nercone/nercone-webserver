FROM python:3.12-slim

WORKDIR /srv/website

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src ./src
RUN uv sync --frozen --no-dev

ENV PATH="/srv/website/.venv/bin:$PATH"
CMD ["nercone-website"]
