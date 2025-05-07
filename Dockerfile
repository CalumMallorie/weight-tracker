FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV INSTANCE_PATH=/app/instance
ENV PORT=8080
ENV LOG_LEVEL=INFO

# Install needed packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gosu && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create app user and directories
RUN mkdir -p /app/data /app/logs /app/instance && \
    groupadd -r weightapp && \
    useradd -r -g weightapp weightapp && \
    chown -R weightapp:weightapp /app/data /app/logs /app/instance

WORKDIR /app

# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Copy migration script
COPY migrate_and_start.sh /migrate_and_start.sh
RUN chmod +x /migrate_and_start.sh

# Set correct permissions
RUN chown -R weightapp:weightapp /app

# Expose the app port
EXPOSE 8080

# Run the entrypoint script
ENTRYPOINT ["/migrate_and_start.sh"] 