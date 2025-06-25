#!/bin/bash
set -e

# Terraform Test Local Run Wrapper Script
# This script orchestrates the complete CID testing workflow

echo "=== CID Terraform Test Local Run ==="
echo "Starting complete test workflow..."

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set default environment variables if not provided
export DATABASE_NAME="${DATABASE_NAME:-cid_data_export}"
export RESOURCE_PREFIX="${RESOURCE_PREFIX:-cid-tf}"
export BACKEND_TYPE="${BACKEND_TYPE:-local}"
export S3_REGION="${S3_REGION:-eu-west-2}"

echo "Configuration:"
echo "- Database Name: $DATABASE_NAME"
echo "- Resource Prefix: $RESOURCE_PREFIX"
echo "- Backend Type: $BACKEND_TYPE"
echo "- AWS Region: $S3_REGION"

# Step 1: Run deployment
echo ""
echo "=== Step 1: Running Deployment ==="
bash "$SCRIPT_DIR/deploy.sh"

# Step 2: Run dashboard checks
echo ""
echo "=== Step 2: Dashboard Validation ==="
if [ -f "$SCRIPT_DIR/.temp_dir" ]; then
  TEMP_DIR=$(cat "$SCRIPT_DIR/.temp_dir")
  if [ -d "$TEMP_DIR" ]; then
    echo "Running dashboard checks..."
    bash "$SCRIPT_DIR/check_dashboards.sh" "$TEMP_DIR"
  else
    echo "Error: Temp directory not found, cannot run dashboard checks"
    exit 1
  fi
else
  echo "Error: No temp directory reference found, cannot run dashboard checks"
  exit 1
fi

# Step 3: Cleanup
echo ""
echo "=== Step 3: Cleanup ==="
bash "$SCRIPT_DIR/cleanup.sh"

echo ""
echo "=== Test Workflow Completed Successfully ==="