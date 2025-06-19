#!/bin/bash
set -e

# Configuration
BACKEND_TYPE=${BACKEND_TYPE:-"local"}  # Can be "local" or "s3"
S3_BUCKET=${S3_BUCKET:-""}
S3_KEY=${S3_KEY:-"terraform/cid-test/terraform.tfstate"}
S3_REGION=${S3_REGION:-"eu-west-2"}  # Default to eu-west-2

# Set AWS region for AWS CLI commands
export AWS_DEFAULT_REGION="${S3_REGION}"
export AWS_REGION="${S3_REGION}"  # Some AWS tools use this variable instead

# Debug region settings
echo "Using AWS region: ${S3_REGION}"
echo "AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}"

# Verify account access
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Get the temp directory from the deploy script
if [ -f "$SCRIPT_DIR/.temp_dir" ]; then
  TEMP_DIR=$(cat "$SCRIPT_DIR/.temp_dir")
  if [ ! -d "$TEMP_DIR" ]; then
    echo "Temp directory $TEMP_DIR not found. Creating a new one..."
    TEMP_DIR=$(mktemp -d)
    PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
    TERRAFORM_DIR="$PROJECT_ROOT/terraform"
    cp -r "$TERRAFORM_DIR"/* "$TEMP_DIR/"
    
    # Configure backend based on environment variable
    if [ -f "$TEMP_DIR/backend.tf" ]; then
      if [ "$BACKEND_TYPE" == "s3" ]; then
        echo "Configuring S3 backend..."
        cat > "$TEMP_DIR/backend.tf" << EOF
terraform {
  backend "s3" {
    bucket = "$S3_BUCKET"
    key    = "$S3_KEY"
    region = "$S3_REGION"
  }
}
EOF
      else
        echo "Configuring local backend..."
        TFSTATE_DIR="$SCRIPT_DIR/tfstate"
        mkdir -p "$TFSTATE_DIR"
        cat > "$TEMP_DIR/backend.tf" << EOF
terraform {
  backend "local" {
    path = "$TFSTATE_DIR/terraform.tfstate"
  }
}
EOF
      fi
    fi
    
    # Initialize Terraform
    cd "$TEMP_DIR"
    terraform init -reconfigure
  fi
else
  echo "No temp directory found from deploy script. Creating a new one..."
  TEMP_DIR=$(mktemp -d)
  PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
  TERRAFORM_DIR="$PROJECT_ROOT/terraform"
  cp -r "$TERRAFORM_DIR"/* "$TEMP_DIR/"
  
  # Configure backend based on environment variable
  if [ -f "$TEMP_DIR/backend.tf" ]; then
    if [ "$BACKEND_TYPE" == "s3" ]; then
      echo "Configuring S3 backend..."
      cat > "$TEMP_DIR/backend.tf" << EOF
terraform {
  backend "s3" {
    bucket = "$S3_BUCKET"
    key    = "$S3_KEY"
    region = "$S3_REGION"
  }
}
EOF
    else
      echo "Configuring local backend..."
      TFSTATE_DIR="$SCRIPT_DIR/tfstate"
      mkdir -p "$TFSTATE_DIR"
      cat > "$TEMP_DIR/backend.tf" << EOF
terraform {
  backend "local" {
    path = "$TFSTATE_DIR/terraform.tfstate"
  }
}
EOF
    fi
  fi
  
  # Initialize Terraform
  cd "$TEMP_DIR"
  terraform init -reconfigure
fi

echo "Cleaning up resources..."

# Get resource prefix from environment variable or use default
RESOURCE_PREFIX=${RESOURCE_PREFIX:-"cid-tf"}

# Empty S3 buckets
echo "Emptying S3 buckets..."
# Look for both default 'cid-' and custom prefix buckets
BUCKETS=$(aws s3api list-buckets --query "Buckets[?contains(Name, '${RESOURCE_PREFIX}-${ACCOUNT_ID}') || contains(Name, 'cid-${ACCOUNT_ID}')].Name" --output text || echo "")

for bucket in $BUCKETS; do
  if [ ! -z "$bucket" ]; then
    echo "Checking if bucket $bucket exists..."
    if aws s3api head-bucket --bucket $bucket 2>/dev/null; then
      echo "Emptying bucket $bucket..."
      # First delete all non-versioned objects
      aws s3 rm s3://$bucket --recursive || true
      
      # Loop to ensure all versioned objects are deleted
      for attempt in {1..3}; do
        echo "Attempt $attempt to delete all versions..."
        
        # Get all versions and delete markers
        VERSIONS=$(aws s3api list-object-versions --bucket $bucket --output json 2>/dev/null || echo '{"Versions":[],"DeleteMarkers":[]}')
        
        # Process versions
        VERSION_COUNT=$(echo "$VERSIONS" | jq -r '.Versions | length // 0')
        # Fix for empty string values
        VERSION_COUNT=${VERSION_COUNT:-0}
        
        if [ "$VERSION_COUNT" -gt 0 ]; then
          echo "Found $VERSION_COUNT versions to delete"
          echo "$VERSIONS" | jq -c '{Objects: [.Versions[] | {Key:.Key, VersionId:.VersionId}] | select(length > 0)}' | aws s3api delete-objects --bucket $bucket --delete file:///dev/stdin || true
        fi
        
        # Process delete markers
        MARKER_COUNT=$(echo "$VERSIONS" | jq -r '.DeleteMarkers | length // 0')
        # Fix for empty string values
        MARKER_COUNT=${MARKER_COUNT:-0}
        
        if [ "$MARKER_COUNT" -gt 0 ]; then
          echo "Found $MARKER_COUNT delete markers to remove"
          echo "$VERSIONS" | jq -c '{Objects: [.DeleteMarkers[] | {Key:.Key, VersionId:.VersionId}] | select(length > 0)}' | aws s3api delete-objects --bucket $bucket --delete file:///dev/stdin || true
        fi
        
        # Check if bucket is empty
        REMAINING=$(aws s3api list-object-versions --bucket $bucket --output json 2>/dev/null || echo '{"Versions":[],"DeleteMarkers":[]}')
        VERSION_COUNT=$(echo "$REMAINING" | jq -r '.Versions | length // 0')
        MARKER_COUNT=$(echo "$REMAINING" | jq -r '.DeleteMarkers | length // 0')
        
        # Fix for empty string values
        VERSION_COUNT=${VERSION_COUNT:-0}
        MARKER_COUNT=${MARKER_COUNT:-0}
        
        if [ "$VERSION_COUNT" -eq 0 ] && [ "$MARKER_COUNT" -eq 0 ]; then
          echo "Bucket is now empty!"
          break
        fi
        
        echo "Bucket still has objects, continuing..."
      done
      
      # Attempt to delete the bucket directly after emptying it
      echo "Attempting to delete bucket $bucket directly..."
      aws s3 rb s3://$bucket --force || true
    fi
  fi
done

# Run terraform destroy
cd "$TEMP_DIR"
echo "Running terraform destroy..."

# Use the override file if it exists
TFVARS_FILES=()
if [ -f "terraform.tfvars" ]; then
  TFVARS_FILES+=("-var-file=terraform.tfvars")
fi
if [ -f "terraform.tfvars.override" ]; then
  TFVARS_FILES+=("-var-file=terraform.tfvars.override")
fi

# Create a temporary tfvars file with the region
if [ -f "$TEMP_DIR/terraform.tfvars" ]; then
  cat > "$TEMP_DIR/region.auto.tfvars" << EOF
global_values = {
  destination_account_id = "$(grep -o 'destination_account_id[[:space:]]*=[[:space:]]*"[^"]*"' "$TEMP_DIR/terraform.tfvars" | cut -d'"' -f2)"
  source_account_ids     = "$(grep -o 'source_account_ids[[:space:]]*=[[:space:]]*"[^"]*"' "$TEMP_DIR/terraform.tfvars" | cut -d'"' -f2)"
  aws_region             = "${S3_REGION}"
  quicksight_user        = "$(grep -o 'quicksight_user[[:space:]]*=[[:space:]]*"[^"]*"' "$TEMP_DIR/terraform.tfvars" | cut -d'"' -f2)"
  cid_cfn_version        = "$(grep -o 'cid_cfn_version[[:space:]]*=[[:space:]]*"[^"]*"' "$TEMP_DIR/terraform.tfvars" | cut -d'"' -f2)"
  data_export_version    = "$(grep -o 'data_export_version[[:space:]]*=[[:space:]]*"[^"]*"' "$TEMP_DIR/terraform.tfvars" | cut -d'"' -f2)"
  environment            = "$(grep -o 'environment[[:space:]]*=[[:space:]]*"[^"]*"' "$TEMP_DIR/terraform.tfvars" | cut -d'"' -f2)"
}
EOF
fi

terraform destroy "${TFVARS_FILES[@]}" -auto-approve
cd "$SCRIPT_DIR"

# Clean up temporary directory
echo "Cleaning up temporary Terraform directory"
rm -rf "$TEMP_DIR"
rm -f "$SCRIPT_DIR/.temp_dir"

echo "Cleanup completed successfully."