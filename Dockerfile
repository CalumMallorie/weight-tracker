FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install needed packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends gosu && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the application (default IDs)
RUN groupadd -r -g 1000 weightapp && useradd -r -u 1000 -g weightapp weightapp

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create entrypoint script to handle permissions properly
RUN echo '#!/bin/bash \n\
# Create directories with proper permissions \n\
mkdir -p /app/data /app/logs \n\
\n\
# Get group and user IDs from environment or use defaults \n\
PUID=${PUID:-1000} \n\
PGID=${PGID:-1000} \n\
\n\
# Update user and group IDs if necessary \n\
if [ "${PUID}" != "1000" ] || [ "${PGID}" != "1000" ]; then \n\
    echo "Setting custom user/group IDs: ${PUID}:${PGID}" \n\
    groupmod -o -g ${PGID} weightapp \n\
    usermod -o -u ${PUID} weightapp \n\
fi \n\
\n\
# Set ownership of application directories \n\
chown -R weightapp:weightapp /app/data /app/logs \n\
chmod -R 755 /app/data /app/logs \n\
\n\
# Execute command as weightapp user \n\
exec gosu weightapp "$@" \n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# Set environment variable for database location (for persistence)
ENV DATABASE_PATH=/app/data/weight_tracker.db

# Expose the port the app runs on
EXPOSE 8080

# Use the custom entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "main.py"] 