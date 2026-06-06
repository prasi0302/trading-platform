FROM python:3.11-slim

WORKDIR /app

# Install shared library
COPY libs/common /tmp/libs/common
RUN pip install --no-cache-dir /tmp/libs/common && rm -rf /tmp/libs

# Install service dependencies
COPY services/order/pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY services/order/app ./app

EXPOSE 8002

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
