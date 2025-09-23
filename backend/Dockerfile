FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./backend/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy application code
COPY . ./backend

# Make scripts executable and fix ownership
RUN chmod +x ./backend/scripts/*.sh ./backend/scripts/*.py

# Create non-root user for security
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Create temporary directory for git operations
RUN mkdir -p /tmp/repo-architect/tmp

# Expose port
EXPOSE 8000

# Start the application directly without fixture loading
CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 