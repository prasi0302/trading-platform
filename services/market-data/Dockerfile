FROM python:3.11-slim

WORKDIR /app

# Install shared library
COPY libs/common /tmp/libs/common
RUN pip install --no-cache-dir /tmp/libs/common && rm -rf /tmp/libs

# Install service dependencies
COPY services/market-data/pyproject.toml .
RUN pip install --no-cache-dir .

# Copy application code
COPY services/market-data/app ./app

EXPOSE 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
