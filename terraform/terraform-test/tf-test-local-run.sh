#!/bin/bash
set -e

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments
BACKEND_TYPE="local"
S3_BUCKET=""
S3_KEY="terraform/cid-test/terraform.tfstate"
S3_REGION="us-east-1"     # Replace with your desired region
SKIP_CLEANUP=false
RESOURCE_PREFIX="cid-tf"  # Default resource prefix for testing

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --s3)
      BACKEND_TYPE="s3"
      shift
      ;;
    --bucket)
      S3_BUCKET="$2"
      shift 2
      ;;
    --key)
      S3_KEY="$2"
      shift 2
      ;;
    --region)
      S3_REGION="$2"
      shift 2
      ;;
    --skip-cleanup)
      SKIP_CLEANUP=true
      shift
      ;;
    --resource-prefix)
      RESOURCE_PREFIX="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: $0 [--s3] [--bucket BUCKET_NAME] [--key KEY_PATH] [--region REGION] [--resource-prefix PREFIX] [--skip-cleanup]"
      exit 1
      ;;
  esac
done

# Validate S3 parameters if using S3 backend
if [ "$BACKEND_TYPE" == "s3" ] && [ -z "$S3_BUCKET" ]; then
  echo "Error: S3 bucket name is required when using S3 backend"
  echo "Usage: $0 --s3 --bucket BUCKET_NAME [--key KEY_PATH] [--region REGION]"
  exit 1
fi

# Export variables for the deploy script
export BACKEND_TYPE="$BACKEND_TYPE"
export S3_BUCKET="$S3_BUCKET"
export S3_KEY="$S3_KEY"
export S3_REGION="$S3_REGION"
export RESOURCE_PREFIX="$RESOURCE_PREFIX"

# Run the deploy script
echo "Running deployment..."
"$SCRIPT_DIR/deploy.sh"

# Ask about cleanup if not skipped
if [ "$SKIP_CLEANUP" = false ]; then
  read -p "Do you want to clean up resources? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Running cleanup..."
    "$SCRIPT_DIR/cleanup.sh"
  else
    echo "Skipping cleanup. Run cleanup.sh manually when ready."
  fi
else
  echo "Skipping cleanup as requested."
fi

echo "Test run completed."