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
# Get group and user IDs from environment variables or use defaults \n\
PUID=${PUID:-1000} \n\
PGID=${PGID:-1000} \n\
\n\
# Change ownership of the application files if needed \n\
if [ "$PUID" != "1000" ] || [ "$PGID" != "1000" ]; then \n\
    echo "Changing ownership of application files to $PUID:$PGID" \n\
    groupmod -o -g "$PGID" weightapp \n\
    usermod -o -u "$PUID" weightapp \n\
    chown -R weightapp:weightapp /app/data /app/logs \n\
else \n\
    chown -R weightapp:weightapp /app/data /app/logs \n\
fi \n\
\n\
# Run the application as the appropriate user \n\
exec gosu weightapp python main.py \n\
' > /entrypoint.sh

RUN chmod +x /entrypoint.sh

# Expose the app port
EXPOSE 8080

# Run the entrypoint script
ENTRYPOINT ["/entrypoint.sh"] 