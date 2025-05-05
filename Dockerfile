FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

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

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .
RUN chown -R weightapp:weightapp /app

# Create a simplified entrypoint script
RUN echo '#!/bin/bash \n\
# Set environment variable for instance path \n\
export INSTANCE_PATH=/app/instance \n\
\n\
# Create directories if they don't exist \n\
mkdir -p /app/data /app/logs /app/instance \n\
\n\
# Run the application \n\
exec python main.py \n\
' > /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Expose the app port
EXPOSE 8080

# Run the entrypoint script
ENTRYPOINT ["/entrypoint.sh"] 