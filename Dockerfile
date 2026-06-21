FROM python:3.12-slim

# Pull the uv binary from astral's official distroless image —
# no curl/pip bootstrap, no extra layers for installing uv itself.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install deps BEFORE copying app code. Docker caches layers by content
# hash — if you copy code first, every code change invalidates the
# deps layer too, and every build re-installs FastAPI/uvicorn from
# scratch. Splitting this way means `uv sync` only re-runs when
# pyproject.toml / uv.lock actually change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY app ./app
RUN uv sync --frozen --no-dev

ENV PATH="/app/.venv/bin:$PATH"

# Don't run the app as root inside the container.
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

EXPOSE 8000

# --proxy-headers + --forwarded-allow-ips: trust X-Forwarded-* headers
# coming from nginx, so request.client.host shows the real visitor IP
# instead of the nginx container's internal IP. Safe here because the
# app port is NOT published to the host — only nginx can reach it.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--proxy-headers", "--forwarded-allow-ips=*"]
