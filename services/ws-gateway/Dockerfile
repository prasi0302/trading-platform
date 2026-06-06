FROM python:3.11-slim

WORKDIR /app

COPY libs/common /tmp/libs/common
RUN pip install --no-cache-dir /tmp/libs/common && rm -rf /tmp/libs

COPY services/ws-gateway/pyproject.toml .
RUN pip install --no-cache-dir .

COPY services/ws-gateway/app ./app

EXPOSE 8005

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
