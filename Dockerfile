# Use Python 3.11 (compatible with all dependencies)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Initialize database at startup (needs DATABASE_URL env var available at runtime), then start the app
CMD ["sh", "-c", "python init_data.py && uvicorn main:app --host 0.0.0.0 --port 8000"]
