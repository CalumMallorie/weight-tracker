#!/bin/bash
set -e

# Create directories if they don't exist
mkdir -p /app/data /app/logs /app/instance

# Fix permissions
chown -R weightapp:weightapp /app/data /app/logs /app/instance

# Check if this is a new container with a mounted old database
if [ -f "/app/data/weight_tracker.db" ]; then
    echo "Detected external database in data directory"
    
    # Create a backup of the original database first
    BACKUP_FILE="/app/data/weight_tracker.db.backup-$(date +%Y%m%d-%H%M%S)"
    echo "Creating backup of original database at ${BACKUP_FILE}"
    cp /app/data/weight_tracker.db "${BACKUP_FILE}"
    
    # Copy the database file to instance directory (the location the app expects)
    echo "Copying database to instance directory for application use"
    cp /app/data/weight_tracker.db /app/instance/weight_tracker.db
    
    # Fix permissions
    chown weightapp:weightapp /app/instance/weight_tracker.db
    chown weightapp:weightapp "${BACKUP_FILE}"
    
    echo "Database copied to instance directory"
    echo "Backup created at ${BACKUP_FILE}"
fi

# Run the application as the proper user
exec gosu weightapp python main.py 