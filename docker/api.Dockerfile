FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

RUN useradd --create-home --uid 10001 appuser

COPY pyproject.toml README.md ./
COPY src ./src
COPY data ./data

RUN pip install --upgrade pip && pip install .

USER appuser

EXPOSE 8000

CMD ["sh", "-c", "uvicorn signalscope.api.main:app --host 0.0.0.0 --port ${PORT}"]
