#!/bin/bash
set -e

# Terraform Test Local Run Wrapper Script
# This script orchestrates the complete CID testing workflow

echo "=== CID Terraform Test Local Run ==="
echo "Starting complete test workflow..."

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Set default environment variables if not provided
export DATABASE_NAME="${DATABASE_NAME:-cid_data_export}"
export RESOURCE_PREFIX="${RESOURCE_PREFIX:-cid-tf}"
export BACKEND_TYPE="${BACKEND_TYPE:-local}"
export S3_REGION="${S3_REGION:-eu-west-2}"

# Local development options (set to true/false)
export BUILD_LOCAL_LAYER="${BUILD_LOCAL_LAYER:-true}"
export USE_LOCAL_CID_TEMPLATE="${USE_LOCAL_CID_TEMPLATE:-true}"
# Single bucket for all local CID assets with organized prefixes
export LOCAL_ASSETS_BUCKET="${LOCAL_ASSETS_BUCKET:-my-cid-test-bucket}"
export LAYER_PREFIX="${LAYER_PREFIX:-cid-resource-lambda-layer}"
export TEMPLATE_PREFIX="${TEMPLATE_PREFIX:-cid-testing/templates}"

echo "Configuration:"
echo "- Database Name: $DATABASE_NAME"
echo "- Resource Prefix: $RESOURCE_PREFIX"
echo "- Backend Type: $BACKEND_TYPE"
echo "- AWS Region: $S3_REGION"
echo "- Build Local Layer: $BUILD_LOCAL_LAYER"
echo "- Use Local CID Template: $USE_LOCAL_CID_TEMPLATE"
echo "- Local Assets Bucket: $LOCAL_ASSETS_BUCKET"
echo "- Layer Prefix: $LAYER_PREFIX"
echo "- Template Prefix: $TEMPLATE_PREFIX"

# Debug region consistency
echo ""
echo "=== Region Debug Info ==="
echo "Current AWS CLI region: $(aws configure get region)"
echo "AWS_DEFAULT_REGION: ${AWS_DEFAULT_REGION:-not set}"
echo "AWS_REGION: ${AWS_REGION:-not set}"
echo "S3_REGION: $S3_REGION"
echo "Account ID: $(aws sts get-caller-identity --query Account --output text)"

# Optional: Build and upload local lambda layer for testing
if [ "${BUILD_LOCAL_LAYER:-false}" = "true" ]; then
  echo ""
  echo "=== Building Local Lambda Layer ==="
  
  # Check if we're in the right directory
  if [ -f "$PROJECT_ROOT/assets/build_lambda_layer.sh" ]; then
    cd "$PROJECT_ROOT"
    echo "Building lambda layer from local code..."
    LAYER_ZIP=$(./assets/build_lambda_layer.sh)
    
    if [ ! -z "$LAYER_ZIP" ] && [ -f "$LAYER_ZIP" ]; then
      echo "Built layer: $LAYER_ZIP"
      
      # Upload to your test bucket if specified
      if [ ! -z "${LOCAL_ASSETS_BUCKET}" ]; then
        # CloudFormation expects bucket name with region suffix
        FULL_BUCKET_NAME="$LOCAL_ASSETS_BUCKET-$S3_REGION"
        echo "Uploading layer to assets bucket: $FULL_BUCKET_NAME/$LAYER_PREFIX"
        aws s3 cp "$LAYER_ZIP" "s3://$FULL_BUCKET_NAME/$LAYER_PREFIX/$LAYER_ZIP"
        echo "Layer uploaded successfully"
        echo "You can now reference: s3://$FULL_BUCKET_NAME/$LAYER_PREFIX/$LAYER_ZIP"
        
        # Set environment variable for deploy script to use local layer bucket
        export LOCAL_LAYER_BUCKET="$LOCAL_ASSETS_BUCKET"
      else
        echo "Layer built locally: $(pwd)/$LAYER_ZIP"
        echo "Set LOCAL_ASSETS_BUCKET environment variable to upload to S3"
      fi
    else
      echo "Error: Failed to build lambda layer"
    fi
    
    cd "$PROJECT_ROOT"
  else
    echo "Error: build_lambda_layer.sh not found at $PROJECT_ROOT/assets/"
  fi
fi

# Step 1: Prepare local CID template (if requested)
if [ "${USE_LOCAL_CID_TEMPLATE:-false}" = "true" ]; then
  echo ""
  echo "=== Preparing Local CID Template ==="
  
  # Check if local cid-cfn.yml exists
  if [ -f "$PROJECT_ROOT/cfn-templates/cid-cfn.yml" ]; then
    echo "Found local cid-cfn.yml, preparing for deployment..."
    
    # Create a temporary S3 location for the local template
    if [ ! -z "${LOCAL_ASSETS_BUCKET}" ]; then
      # Use full bucket name with region suffix for template upload
      FULL_BUCKET_NAME="$LOCAL_ASSETS_BUCKET-$S3_REGION"
      echo "Uploading local cid-cfn.yml to: s3://$FULL_BUCKET_NAME/$TEMPLATE_PREFIX/"
      aws s3 cp "$PROJECT_ROOT/cfn-templates/cid-cfn.yml" "s3://$FULL_BUCKET_NAME/$TEMPLATE_PREFIX/cid-cfn.yml"
      
      # Set environment variable to modify the template URL in deploy script
      export LOCAL_CID_TEMPLATE_URL="https://$FULL_BUCKET_NAME.s3.amazonaws.com/$TEMPLATE_PREFIX/cid-cfn.yml"
      echo "Local template URL: $LOCAL_CID_TEMPLATE_URL"
    else
      echo "Warning: LOCAL_ASSETS_BUCKET not set. Using local file path."
      export LOCAL_CID_TEMPLATE_PATH="$PROJECT_ROOT/cfn-templates/cid-cfn.yml"
    fi
  else
    echo "Warning: cfn-templates/cid-cfn.yml not found at $PROJECT_ROOT/cfn-templates/. Using remote template."
  fi
fi

# Step 2: Run deployment
echo ""
echo "=== Step 2: Running Deployment ==="
bash "$SCRIPT_DIR/deploy.sh"

# Step 3: Run dashboard checks
echo ""
echo "=== Step 3: Dashboard Validation ==="
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

# Step 4: Cleanup
echo ""
echo "=== Step 4: Cleanup ==="
echo "The deployment and testing is complete."
echo "Do you want to clean up the deployed resources? This will:"
echo "- Empty S3 data buckets"
echo "- Run 'terraform destroy' to remove all CID resources"
echo "- Clean up temporary files"
echo ""
read -p "Proceed with cleanup? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting cleanup..."
    bash "$SCRIPT_DIR/cleanup.sh"
else
    echo "Cleanup skipped. Resources remain deployed."
    echo "To clean up later, run: bash $SCRIPT_DIR/cleanup.sh"
fi

echo ""
echo "=== Test Workflow Completed Successfully ==="