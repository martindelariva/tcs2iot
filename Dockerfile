# Slim Python base. awscrt ships prebuilt wheels for linux, so no compiler needed.
FROM python:3.12-slim

# Don't buffer stdout/stderr so container logs appear in real time.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code.
COPY src/ /app/src/

WORKDIR /app/src

# Default command runs the processor; overridden per-service in compose.
CMD ["python", "processor.py"]
