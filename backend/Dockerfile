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
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Make scripts executable
RUN chmod +x ./scripts/*.sh ./scripts/*.py

# Create temporary directory for git operations
RUN mkdir -p /tmp/repo-architect/tmp

# Expose port
EXPOSE 8000

# Render startup command (simplified)
CMD ["./scripts/startup.prod.sh"]
