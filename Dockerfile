# Use a lightweight Python base image
FROM python:3.11-slim-bookworm

# Set environment variables to optimize Python execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    MCP_SERVER_HOST=0.0.0.0 \
    MCP_SERVER_PORT=8000

# Set the working directory
WORKDIR /app

# Install system dependencies required for building python packages (if needed by numpy/scipy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project source code
COPY src/ ./src/

# Expose the designated MCP port
EXPOSE 8000

# Define the entry point, executing the main server module
CMD ["python", "-m", "src.main"]