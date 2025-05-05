FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create a non-root user to run the application
RUN groupadd -r weightapp && useradd -r -g weightapp weightapp

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories and set permissions
RUN mkdir -p /app/data /app/logs && \
    chown -R weightapp:weightapp /app/data /app/logs

# Set environment variable for database location (for persistence)
ENV DATABASE_PATH=/app/data/weight_tracker.db

# Expose the port the app runs on
EXPOSE 8080

# Switch to non-root user
USER weightapp

# Run the application
CMD ["python", "main.py"] 