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

# Verify account access
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Get the script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
TERRAFORM_DIR="$PROJECT_ROOT/cicd-deployment"

# Create a temporary directory for modified Terraform files
TEMP_DIR=$(mktemp -d)
echo "Creating temporary Terraform directory at $TEMP_DIR"

# Copy Terraform files to temporary directory
cp -r "$TERRAFORM_DIR"/* "$TEMP_DIR/"

# Create a directory to store the tfstate file
TFSTATE_DIR="$SCRIPT_DIR/tfstate"
mkdir -p "$TFSTATE_DIR"

# Set default resource prefix if not provided
RESOURCE_PREFIX=${RESOURCE_PREFIX:-"cid-tf"}
echo "Using resource prefix: ${RESOURCE_PREFIX}"

# Modify variables.tf to change the default resource prefix
echo "Modifying variables.tf to use resource prefix: ${RESOURCE_PREFIX}"
if [ -f "$TEMP_DIR/variables.tf" ]; then
  # Update only the resource_prefix in cid_dataexports_destination default section
  sed -i.bak "s/resource_prefix  = \"cid\"/resource_prefix  = \"${RESOURCE_PREFIX}\"/g" "$TEMP_DIR/variables.tf"
  
  # Verify the change
  echo "Verifying change in variables.tf:"
  grep -A1 "resource_prefix  = " "$TEMP_DIR/variables.tf" | head -2
fi

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
    cat > "$TEMP_DIR/backend.tf" << EOF
terraform {
  backend "local" {
    path = "$TFSTATE_DIR/terraform.tfstate"
  }
}
EOF
  fi
fi

# Modify provider.tf to use the same account for both providers and set region
cat > "$TEMP_DIR/local_override.tf" << EOF
provider "aws" {
  region = "${S3_REGION}"
}

provider "aws" {
  alias  = "destination_account"
  region = "${S3_REGION}"
}

terraform {
  required_version = ">= 1.0.0"
}
EOF

# Debug region settings
echo "Using AWS region: ${S3_REGION}"
echo "AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION}"

# First check if the file exists and what it contains
echo "Examining main.tf file..."
if [ -f "$TEMP_DIR/main.tf" ]; then
  # Create a backup of the original file
  cp "$TEMP_DIR/main.tf" "$TEMP_DIR/main.tf.original"
  
  # Use grep to find the resource and then use awk to comment it out
  grep -n "resource \"aws_cloudformation_stack\" \"cid_dataexports_source\"" "$TEMP_DIR/main.tf" | while read -r line; do
    line_num=$(echo "$line" | cut -d: -f1)
    echo "Found cid_dataexports_source at line $line_num"
    
    # Use awk to comment out the resource block
    awk -v line="$line_num" 'NR==line {print "# SKIPPED FOR LOCAL TESTING\n# " $0; next} {print}' "$TEMP_DIR/main.tf.original" > "$TEMP_DIR/main.tf.tmp"
    mv "$TEMP_DIR/main.tf.tmp" "$TEMP_DIR/main.tf"
    
    # Find the closing brace of the resource block
    end_line=$(tail -n +$line_num "$TEMP_DIR/main.tf" | grep -n "^}" | head -1 | cut -d: -f1)
    end_line=$((line_num + end_line - 1))
    echo "Resource block ends at line $end_line"
    
    # Comment out all lines in the resource block
    awk -v start="$line_num" -v end="$end_line" 'NR>start && NR<=end {print "# " $0; next} {print}' "$TEMP_DIR/main.tf" > "$TEMP_DIR/main.tf.tmp"
    mv "$TEMP_DIR/main.tf.tmp" "$TEMP_DIR/main.tf"
  done
  
  # Update dependencies
  sed -i.bak 's/aws_cloudformation_stack.cid_dataexports_source,/# aws_cloudformation_stack.cid_dataexports_source,/g' "$TEMP_DIR/main.tf"
else
  echo "Error: main.tf not found in $TEMP_DIR"
  exit 1
fi

# Check and modify outputs.tf to remove references to deleted resources
if [ -f "$TEMP_DIR/outputs.tf" ]; then
  echo "Modifying outputs.tf to remove references to deleted resources..."
  
  # Find and remove the output block for cid_dataexports_source_outputs
  grep -n "output \"cid_dataexports_source_outputs\"" "$TEMP_DIR/outputs.tf" | while read -r line; do
    line_num=$(echo "$line" | cut -d: -f1)
    echo "Found cid_dataexports_source_outputs at line $line_num"
    
    # Find the closing brace of the output block
    end_line=$(tail -n +$line_num "$TEMP_DIR/outputs.tf" | grep -n "^}" | head -1 | cut -d: -f1)
    end_line=$((line_num + end_line - 1))
    echo "Output block ends at line $end_line"
    
    # Remove the entire output block
    sed -i.bak "${line_num},${end_line}d" "$TEMP_DIR/outputs.tf"
  done
fi

# Deploy with Terraform
cd "$TEMP_DIR"
echo "Initializing Terraform..."
terraform init -reconfigure

# Use terraform.tfvars if it exists
TFVARS_FILES=()
if [ -f "terraform.tfvars" ]; then
  TFVARS_FILES+=("-var-file=terraform.tfvars")
fi

# Import existing resources if state file is empty and using local backend
if [ "$BACKEND_TYPE" == "local" ]; then
  if [ ! -f "$TFSTATE_DIR/terraform.tfstate" ] || [ ! -s "$TFSTATE_DIR/terraform.tfstate" ]; then
    echo "No existing state file found or it's empty. Creating new state..."
  else
    echo "Found existing state file. Refreshing state..."
    terraform refresh
  fi
fi

echo "Planning Terraform deployment..."
terraform plan "${TFVARS_FILES[@]}" -out=tfplan

echo "Applying Terraform plan..."
terraform apply -auto-approve tfplan

# Extract dashboard variables directly from variables.tf file
cd "$TEMP_DIR"
echo "Extracting dashboard settings from Terraform configuration..."

# Extract values using grep and sed - improved patterns to better match the structure
deploy_cudos_v5=$(grep -A30 'cudos_dashboard' variables.tf | grep 'deploy_cudos_v5' | grep -o '"yes"' | tr -d '"' || echo "no")
deploy_cost_intelligence_dashboard=$(grep -A30 'cudos_dashboard' variables.tf | grep 'deploy_cost_intelligence_dashboard' | grep -o '"yes"' | tr -d '"' || echo "no")
deploy_kpi_dashboard=$(grep -A30 'cudos_dashboard' variables.tf | grep 'deploy_kpi_dashboard' | grep -o '"yes"' | tr -d '"' || echo "no")

# Check if there's a terraform.tfvars file that might override the defaults
if [ -f "terraform.tfvars" ]; then
  echo "Found terraform.tfvars, checking for overrides..."
  if grep -q "deploy_cudos_v5" terraform.tfvars; then
    deploy_cudos_v5=$(grep "deploy_cudos_v5" terraform.tfvars | cut -d'=' -f2 | tr -d ' "' || echo "$deploy_cudos_v5")
  fi
  if grep -q "deploy_cost_intelligence_dashboard" terraform.tfvars; then
    deploy_cost_intelligence_dashboard=$(grep "deploy_cost_intelligence_dashboard" terraform.tfvars | cut -d'=' -f2 | tr -d ' "' || echo "$deploy_cost_intelligence_dashboard")
  fi
  if grep -q "deploy_kpi_dashboard" terraform.tfvars; then
    deploy_kpi_dashboard=$(grep "deploy_kpi_dashboard" terraform.tfvars | cut -d'=' -f2 | tr -d ' "' || echo "$deploy_kpi_dashboard")
  fi
fi

# Export the variables
export deploy_cudos_v5
export deploy_cost_intelligence_dashboard
export deploy_kpi_dashboard

# Echo the dashboard settings
echo "Dashboard settings from Terraform configuration:"
echo "- cudos-v5: $deploy_cudos_v5"
echo "- cost_intelligence_dashboard: $deploy_cost_intelligence_dashboard"
echo "- kpi_dashboard: $deploy_kpi_dashboard"

cd "$PROJECT_ROOT"

# Set database name
export database_name="${DATABASE_NAME:-cid_data_export}"
echo "Using database name: $database_name"

# Run BATS tests
echo "Running dashboard tests..."
cd "$SCRIPT_DIR"
bats dashboards.bats
echo "=== Dashboard Test Results ==="
if [ -f "/tmp/cudos_test/test_output.log" ]; then
  cat "/tmp/cudos_test/test_output.log"
else
  echo "Test log file not found"
fi
echo "=== End of Test Results ==="

# Save the temp directory path for cleanup script
echo "$TEMP_DIR" > "$SCRIPT_DIR/.temp_dir"
echo "Deployment completed successfully."
