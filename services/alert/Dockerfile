FROM python:3.11-slim

WORKDIR /app

COPY libs/common /tmp/libs/common
RUN pip install --no-cache-dir /tmp/libs/common && rm -rf /tmp/libs

COPY services/alert/pyproject.toml .
RUN pip install --no-cache-dir .

COPY services/alert/app ./app

# Run as non-root user
RUN useradd -r -s /bin/false appuser
USER appuser

EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
