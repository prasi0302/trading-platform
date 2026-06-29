FROM python:3.11-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install shared library
COPY libs/common /tmp/libs/common
RUN pip install --no-cache-dir /tmp/libs/common && rm -rf /tmp/libs

# Install service dependencies
COPY services/order/pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY services/order/app ./app

# Run as non-root user
RUN useradd -r -s /bin/false appuser
USER appuser

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD ["curl", "-fsS", "http://127.0.0.1:8002/health"]

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
