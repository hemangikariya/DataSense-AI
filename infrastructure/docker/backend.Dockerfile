FROM python:3.12-slim

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --timeout 1000 --retries 10 torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir --timeout 1000 --retries 10 --index-url https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# Copy source code files
COPY backend/src /app/src
COPY backend/alembic /app/alembic
COPY backend/alembic.ini /app/alembic.ini

EXPOSE 8000

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
