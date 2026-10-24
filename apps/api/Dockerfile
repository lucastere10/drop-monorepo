FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# /opt/drop stays intact when Cloud Build mounts the source over /workspace.
WORKDIR /opt/drop

RUN apt-get update && apt-get install -y --no-install-recommends curl build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir uv

COPY pyproject.toml /opt/drop/pyproject.toml
COPY packages /opt/drop/packages
COPY apps/api /opt/drop/apps/api

WORKDIR /opt/drop/apps/api
RUN uv sync --all-extras

ENV PATH="/opt/drop/apps/api/.venv/bin:$PATH" \
    DROP_ENV=prod \
    DJANGO_SETTINGS_MODULE=setup.settings.production \
    LOCAL_STORAGE_ROOT=/data/uploads \
    PYTHONPATH=/opt/drop/apps/api

RUN mkdir -p /data/uploads

EXPOSE 8080
CMD ["sh", "-c", "uv run python manage.py migrate --noinput && uv run gunicorn setup.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 2"]
