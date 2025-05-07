#!/bin/bash

# Main Docker test workflow script
# This script runs all Docker-related tests to ensure the application works correctly

set -e

echo "======================================================"
echo "       WEIGHT TRACKER DOCKER TEST WORKFLOW            "
echo "======================================================"

# Step 1: Run unit tests
echo "Step 1: Running unit tests..."
python -m pytest
echo "✅ Unit tests passed!"

# Step 2: Basic Docker build and functionality test
echo -e "\nStep 2: Testing basic Docker functionality..."
./docker_test.sh
echo "✅ Basic Docker functionality test passed!"

# Step 3: Database migration test
echo -e "\nStep 3: Testing database migration in Docker..."
./docker_migration_test.sh --skip-build  # We already built the image in step 2
echo "✅ Database migration test passed!"

echo -e "\n======================================================"
echo "       ALL DOCKER TESTS PASSED SUCCESSFULLY!            "
echo "======================================================"
echo "The Docker image is ready for production use!" 