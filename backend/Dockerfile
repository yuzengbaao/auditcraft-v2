# AuditCraft v2 Backend Dockerfile
# Build: docker build -t auditcraft-backend .
# Run:   docker run -p 8000:8000 auditcraft-backend

FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system build dependencies for py-solc-x and general compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libffi-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-install solc compiler (avoids runtime download)
RUN python3 -c "from solcx import install_solc; install_solc('0.8.19')" || echo "solc install skipped - will retry at runtime"

# Copy application code
COPY . .

# Expose FastAPI default port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
