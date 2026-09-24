# syntax=docker/dockerfile:1
FROM python:3.12-slim AS base
WORKDIR /app
RUN useradd --create-home --uid 10001 dolphin
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .
USER dolphin
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
