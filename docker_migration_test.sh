#!/bin/bash

# Test script for database migration in Docker
# This script builds the Docker image, runs it with an old database, and verifies migration works

set -e

echo "===== WEIGHT TRACKER MIGRATION TEST ====="

# Build the Docker image if not specified otherwise
if [ "$1" != "--skip-build" ]; then
  echo "Building Docker image..."
  docker build -t weight-tracker-test .
fi

# Create directories if they don't exist
mkdir -p docker_test_data docker_test_logs docker_test_instance

# Copy our test database to the Docker test directory
echo "Preparing test database..."
cp test_data/old_database.db docker_test_data/weight_tracker.db

# Clean up any previous test container
echo "Cleaning up any previous test containers..."
docker rm -f weight-tracker-migration-test 2>/dev/null || true

echo "Starting Docker container with the test database..."
# Run the Docker container with the test database mounted
docker run -d \
  --name weight-tracker-migration-test \
  -p 8081:8080 \
  -v "$(pwd)/docker_test_data:/app/data" \
  -v "$(pwd)/docker_test_logs:/app/logs" \
  -v "$(pwd)/docker_test_instance:/app/instance" \
  -e DATABASE_PATH=/app/data/weight_tracker.db \
  weight-tracker-test

# Wait for the container to initialize
echo "Waiting for container to initialize..."
sleep 5

# Check if the app is running
echo "Checking if app is running..."
HEALTH_OK=false
for i in {1..5}; do
  if curl -s -f http://localhost:8081/ > /dev/null; then
    echo "✅ App is running successfully!"
    HEALTH_OK=true
    break
  else
    echo "Health check failed, retrying in 2 seconds..."
    sleep 2
  fi
done

if [ "$HEALTH_OK" != "true" ]; then
  echo "❌ App failed to start properly"
  docker logs weight-tracker-migration-test
  docker rm -f weight-tracker-migration-test
  exit 1
fi

# Check the database schema
echo "Checking final database schema..."
SCHEMA_CHECK=$(sqlite3 docker_test_data/weight_tracker.db "PRAGMA table_info(weight_category);")

if [ -n "$SCHEMA_CHECK" ]; then
  echo "✅ Migration successful! Schema verified."
  echo "$SCHEMA_CHECK"
else
  echo "❌ Migration failed! Could not find expected tables."
  docker logs weight-tracker-migration-test
  docker rm -f weight-tracker-migration-test
  exit 1
fi

# Clean up
echo "Cleaning up..."
docker rm -f weight-tracker-migration-test

echo "===== MIGRATION TEST COMPLETED SUCCESSFULLY =====" 