# CID Terraform Testing Framework

This directory contains scripts for testing Cloud Intelligence Dashboards (CID) deployments using Terraform with local development capabilities.

## Overview

The testing framework provides a complete workflow for:
- Building and testing local CID code changes
- Using local CloudFormation templates
- Deploying CID infrastructure via Terraform
- Validating dashboard deployments
- Cleaning up test resources

## Scripts

### Main Scripts

- **`tf-test-local-run.sh`** - Main wrapper script that orchestrates the complete testing workflow
- **`deploy.sh`** - Handles Terraform deployment with local asset support
- **`check_dashboards.sh`** - Validates deployed dashboards and runs tests
- **`cleanup.sh`** - Cleans up deployed resources and S3 buckets

### Usage

```bash
# Complete workflow (recommended)
bash tf-test-local-run.sh
```

## Configuration

### Environment Variables

Set these variables to customize your testing environment:

```bash
# Basic Configuration
export DATABASE_NAME="cid_data_export"           # Database name for CID
export RESOURCE_PREFIX="cid-tf"                  # Prefix for AWS resources
export BACKEND_TYPE="local"                      # Terraform backend type ("local" or "s3")
export S3_REGION="eu-west-2"                     # AWS region for deployment

# S3 Backend Configuration (only needed if BACKEND_TYPE="s3")
export S3_BUCKET="my-terraform-state-bucket"     # S3 bucket for Terraform state
export S3_KEY="terraform/cid-test/terraform.tfstate"  # S3 key for state file
export BACKEND_REGION="us-east-1"                # Region where backend bucket exists

# Local Development Options
export BUILD_LOCAL_LAYER="true"                  # Build local lambda layer
export USE_LOCAL_CID_TEMPLATE="true"             # Use local CID template
export LOCAL_ASSETS_BUCKET="my-cid-test-bucket"  # S3 bucket for local assets

# Advanced Options (DO NOT CHANGE)
export LAYER_PREFIX="cid-resource-lambda-layer"  # S3 prefix for lambda layers (required by CloudFormation)
export TEMPLATE_PREFIX="cid-testing/templates"   # S3 prefix for templates
```

### S3 Bucket Configuration

**Important**: The CloudFormation template automatically adds the region suffix to your bucket name.

If your bucket is named `my-cid-test-bucket-eu-west-2`, set:
```bash
export LOCAL_ASSETS_BUCKET="my-cid-test-bucket"  # Without region suffix
```

The script will automatically upload to `my-cid-test-bucket-eu-west-2`.

**Note**: The `LAYER_PREFIX` must remain as `cid-resource-lambda-layer` as this is required by the CloudFormation template.

### Terraform Variables Configuration

Create a `terraform.tfvars` file in the `terraform/cicd-deployment` directory with your configuration:

```hcl
# terraform/cicd-deployment/terraform.tfvars
global_values = {
  destination_account_id = "123456789012"      # Your AWS account ID (12 digits)
  source_account_ids     = "123456789012"      # Same account ID for single-account testing
  aws_region             = "eu-west-2"         # AWS region for deployment
  quicksight_user        = "your-username"     # Your QuickSight username
  cid_cfn_version        = "4.2.6"             # CID CloudFormation version
  data_export_version    = "0.5.0"             # Data Export version
  environment            = "dev"               # Environment (dev, staging, prod)
}

# Optional: Customize dashboard deployment
cloud_intelligence_dashboards = {
  deploy_cudos_v5                    = "yes"
  deploy_cost_intelligence_dashboard = "yes"
  deploy_kpi_dashboard               = "yes"
  deploy_tao_dashboard               = "no"
  deploy_compute_optimizer_dashboard = "no"
}
```

**Important Notes:**
- Replace `123456789012` with your actual AWS account ID
- Replace `your-username` with your QuickSight username
- For single-account testing, use the same account ID for both `destination_account_id` and `source_account_ids`
- The framework automatically handles single-account deployment by skipping the source stack

## Local Development Features

### 1. Local Lambda Layer Testing

When `BUILD_LOCAL_LAYER=true`:
- Builds lambda layer from your local CID code using `assets/build_lambda_layer.sh`
- Uploads to S3 at `s3://my-cid-test-bucket-region/cid-resource-lambda-layer/cid-X.X.X.zip`
- CloudFormation uses your local layer instead of the official AWS-managed layer

### 2. Local CloudFormation Template Testing

When `USE_LOCAL_CID_TEMPLATE=true`:
- Uploads your local `cfn-templates/cid-cfn.yml` to S3
- Terraform uses your local template instead of the remote version
- Data exports template still uses the official remote version

### 3. Terraform Backend Options

**Local Backend (default)**:
- Stores Terraform state locally in `tfstate/terraform.tfstate`
- No additional configuration required
- Suitable for individual testing

**S3 Backend**:
- Stores Terraform state in S3 for team collaboration
- Requires `S3_BUCKET`, `S3_KEY`, and `BACKEND_REGION` variables
- Supports cross-region setup (backend in us-east-1, resources in eu-west-2)

```bash
# Example S3 backend configuration
export BACKEND_TYPE="s3"
export S3_BUCKET="my-terraform-state-bucket"
export S3_KEY="terraform/cid-test/terraform.tfstate"
export BACKEND_REGION="us-east-1"  # Where your state bucket exists
export S3_REGION="eu-west-2"       # Where CID resources will be deployed
```

## Workflow Steps

### 1. Local Asset Preparation
- Builds local lambda layer (if enabled)
- Uploads local CID template (if enabled)
- Sets up environment variables for deployment

### 2. Terraform Deployment
- Creates temporary Terraform configuration
- Modifies variables to use local assets
- Deploys CID infrastructure
- Skips source account stack for local testing

### 3. Dashboard Validation
- Extracts dashboard configuration from Terraform
- Runs BATS tests to validate deployments
- Checks QuickSight dashboard availability

### 4. Resource Cleanup
- Empties S3 data buckets (preserves buckets)
- Runs `terraform destroy`
- Cleans up temporary files
- Removes any remaining resources

## Testing Scenarios

### Scenario 1: Test Local Code Changes
```bash
export BUILD_LOCAL_LAYER="true"
export USE_LOCAL_CID_TEMPLATE="false"
bash tf-test-local-run.sh
```

### Scenario 2: Test Local Template Changes
```bash
export BUILD_LOCAL_LAYER="false"
export USE_LOCAL_CID_TEMPLATE="true"
bash tf-test-local-run.sh
```

### Scenario 3: Test Both Local Changes
```bash
export BUILD_LOCAL_LAYER="true"
export USE_LOCAL_CID_TEMPLATE="true"
bash tf-test-local-run.sh
```

### Scenario 4: Use Official Assets
```bash
export BUILD_LOCAL_LAYER="false"
export USE_LOCAL_CID_TEMPLATE="false"
bash tf-test-local-run.sh
```

## Dashboard Testing

The framework includes dedicated dashboard validation through the `check_dashboards.sh` script, which is automatically executed as part of the main workflow.

Features:
- Extracts dashboard settings from Terraform configuration
- Validates QuickSight dashboard deployments
- Runs comprehensive BATS test suite
- Provides detailed test results and logs

## Prerequisites

### Required Tools
- AWS CLI configured with appropriate permissions
- Terraform >= 1.0.0
- BATS (Bash Automated Testing System)
- jq (JSON processor)
- Python 3.x (for lambda layer building)

### AWS Permissions
Your AWS credentials need permissions for:
- **CloudFormation** (stack create/delete/describe operations)
- **S3** (bucket create/delete, object upload/download, versioning, lifecycle)
- **Glue** (database/table/crawler create/delete/start operations)
- **Athena** (workgroup create/delete, query execution)
- **Lambda** (function create/delete, layer publish/delete)
- **QuickSight** (full access for dashboards, datasets, datasources, users)
- **IAM** (role/policy create/delete/attach, PassRole)
- **CUR** (Cost and Usage Report definition operations)
- **BCM Data Exports** (Billing and Cost Management data exports)
- **KMS** (key operations for encryption/decryption)
- **CloudWatch Logs** (log group/stream creation for Lambda functions)

**Note**: The framework requires extensive permissions as it creates a complete CID infrastructure including data pipelines, dashboards, and associated AWS resources.

### S3 Bucket Setup
- Create an S3 bucket for storing local assets
- Ensure the bucket name follows the pattern: `my-cid-test-bucket-region`
- The bucket should be in the same region as your deployment

## Troubleshooting

### Common Issues

1. **"NoSuchBucket" Error**
   - Ensure your `LOCAL_ASSETS_BUCKET` is set without the region suffix
   - Verify the bucket exists in the target region

2. **Lambda Layer Validation Error**
   - Check that the bucket name doesn't contain forward slashes
   - Ensure the layer is uploaded to the correct S3 path

3. **Region Mismatch**
   - Verify `S3_REGION` matches your deployment region
   - Check AWS CLI default region configuration

4. **Permission Errors**
   - Ensure your AWS credentials have all required permissions
   - Check IAM policies for CUR, QuickSight, and other services

### Debug Information

The script provides detailed debug output including:
- Current AWS CLI region settings
- Environment variable values
- S3 upload paths and URLs
- Terraform configuration changes

## CI/CD Integration

For GitHub Actions or other CI/CD systems, use the main wrapper script:

```yaml
- name: Run CID Testing Workflow
  run: |
    export BUILD_LOCAL_LAYER="true"
    export USE_LOCAL_CID_TEMPLATE="true"
    export LOCAL_ASSETS_BUCKET="my-cid-test-bucket"
    bash terraform/terraform-test/tf-test-local-run.sh
```

## File Structure

```
terraform-test/
├── README.md                 # This documentation
├── tf-test-local-run.sh     # Main wrapper script
├── deploy.sh                # Terraform deployment
├── check_dashboards.sh      # Dashboard validation
├── cleanup.sh               # Resource cleanup
├── dashboards.bats          # BATS test suite
└── tfstate/                 # Local Terraform state (created)
```

## Support

For issues or questions:
1. Check the debug output for detailed error information
2. Verify all prerequisites are installed and configured
3. Ensure AWS permissions are correctly set up
4. Review the CloudWatch logs for Lambda execution details