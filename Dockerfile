FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies (SQLite, etc.)
RUN apt-get update && apt-get install -y sqlite3 && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Environment variables
ENV PYTHONUNBUFFERED=1

# Default command (overridden in docker-compose)
CMD ["python", "flask_backend.py"]