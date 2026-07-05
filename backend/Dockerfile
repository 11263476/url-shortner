FROM python:3.12-slim AS builder

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir hatchling build
COPY . .
RUN python -m build --wheel
RUN python -m compileall src

FROM python:3.12-slim

WORKDIR /app
RUN addgroup --system --gid 1001 app \
    && adduser --system --uid 1001 --gid 1001 app
COPY --from=builder /app/dist/*.whl /tmp/
RUN pip install --no-cache-dir /tmp/*.whl && rm -rf /tmp/*.whl
USER app

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
