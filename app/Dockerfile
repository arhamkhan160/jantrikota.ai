# Base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (important for ML libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI.
# main.py is at /app/main.py and imports top-level modules (core.*, api.*),
# so the module path is `main:app`, not `app.main:app`.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]