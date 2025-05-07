#!/bin/bash

# Test script for migrating user data from persistent_volume_from_user
# This script builds the Docker image, runs it with the user's database, and verifies migration works

set -e

echo "===== WEIGHT TRACKER USER DB MIGRATION TEST ====="

# Build the Docker image
echo "Building Docker image..."
docker build -t weight-tracker-test .

# Create temporary directories for the test
echo "Creating temporary directories..."
mkdir -p test_user_migration/data test_user_migration/logs test_user_migration/instance

# Copy user database to test directory
echo "Copying user database for testing..."
cp persistent_volume_from_user/instance/weight_tracker.db test_user_migration/data/weight_tracker.db

# Clean up any previous test container
echo "Cleaning up any previous test containers..."
docker rm -f weight-tracker-user-migration-test 2>/dev/null || true

echo "Starting Docker container with user database..."
# Run the Docker container with the test database mounted
docker run -d \
  --name weight-tracker-user-migration-test \
  -p 8082:8080 \
  -v "$(pwd)/test_user_migration/data:/app/data" \
  -v "$(pwd)/test_user_migration/logs:/app/logs" \
  -v "$(pwd)/test_user_migration/instance:/app/instance" \
  weight-tracker-test

# Wait for the container to initialize
echo "Waiting for container to initialize..."
sleep 5

# Check if the app is running
echo "Checking if app is running..."
HEALTH_OK=false
for i in {1..5}; do
  if curl -s -f http://localhost:8082/ > /dev/null; then
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
  docker logs weight-tracker-user-migration-test
  docker rm -f weight-tracker-user-migration-test
  exit 1
fi

# Verify the database was migrated successfully
echo "Verifying database migration..."
if [ -f "test_user_migration/instance/weight_tracker.db" ]; then
  echo "✅ Database was copied to instance directory"
  
  # Check if a backup was created
  BACKUP_COUNT=$(ls test_user_migration/data/weight_tracker.db.backup-* 2>/dev/null | wc -l)
  if [ "$BACKUP_COUNT" -gt 0 ]; then
    echo "✅ Database backup was created in data directory"
  else
    echo "❌ No database backup was created"
    docker logs weight-tracker-user-migration-test
    docker rm -f weight-tracker-user-migration-test
    exit 1
  fi
  
  # Check schema of migrated database
  echo "Checking database schema..."
  SCHEMA_CHECK=$(sqlite3 test_user_migration/instance/weight_tracker.db "PRAGMA table_info(weight_category);")
  
  if grep -q "is_body_weight" <<< "$SCHEMA_CHECK"; then
    echo "✅ Migration successful! Schema has been updated."
    echo "$SCHEMA_CHECK"
  else
    echo "❌ Migration failed! Schema was not updated correctly."
    docker logs weight-tracker-user-migration-test
    docker rm -f weight-tracker-user-migration-test
    exit 1
  fi
else
  echo "❌ Database was not copied to instance directory"
  docker logs weight-tracker-user-migration-test
  docker rm -f weight-tracker-user-migration-test
  exit 1
fi

# Clean up
echo "Cleaning up..."
docker rm -f weight-tracker-user-migration-test

echo "===== USER MIGRATION TEST COMPLETED SUCCESSFULLY =====" 