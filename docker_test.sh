#!/bin/bash

# Docker container test script
# This script builds the Docker image, runs it, and performs basic health checks

set -e

echo "===== WEIGHT TRACKER DOCKER TEST ====="

# Build the Docker image
echo "Building Docker image..."
docker build -t weight-tracker-test .

# Create test directories if they don't exist
mkdir -p docker_test_data
mkdir -p docker_test_logs
mkdir -p docker_test_instance

# Clean up any previous test container
echo "Cleaning up any previous test containers..."
docker rm -f weight-tracker-test 2>/dev/null || true

# Run the container
echo "Starting container..."
docker run -d --name weight-tracker-test \
  -p 8088:8080 \
  -v "$(pwd)/docker_test_data:/app/data" \
  -v "$(pwd)/docker_test_logs:/app/logs" \
  -v "$(pwd)/docker_test_instance:/app/instance" \
  weight-tracker-test

# Wait for container to start and initialize
echo "Waiting for container to initialize..."
sleep 5

# Perform health check
echo "Performing health check..."
for i in {1..5}; do
  if curl -s -f http://localhost:8088/ > /dev/null; then
    echo "✅ Health check passed!"
    HEALTH_OK=true
    break
  else
    echo "Health check failed, retrying in 2 seconds..."
    sleep 2
  fi
done

if [ "$HEALTH_OK" != "true" ]; then
  echo "❌ Health check failed after 5 attempts"
  echo "Container logs:"
  docker logs weight-tracker-test
  docker rm -f weight-tracker-test
  exit 1
fi

# Check database is created
echo "Checking if database was created..."
if [ -f "docker_test_data/weight_tracker.db" ]; then
  echo "✅ Database created successfully"
else
  echo "❌ Database was not created"
  docker logs weight-tracker-test
  docker rm -f weight-tracker-test
  exit 1
fi

# Clean up
echo "Cleaning up test container..."
docker rm -f weight-tracker-test

echo "===== TEST COMPLETED SUCCESSFULLY ====="
echo "The Docker image is working correctly!" 