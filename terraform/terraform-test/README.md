# Local Testing for Cloud Intelligence Dashboards

This document provides instructions for local testing of the AWS Cloud Intelligence Dashboards (CID) Terraform deployment.

## Overview

The testing framework now uses a modular approach with three scripts:

1. **tf-test-local-run.sh**: The main entry script that:
   - Processes command-line arguments for backend configuration
   - Sets environment variables for the other scripts
   - Calls the deploy script
   - Optionally calls the cleanup script based on user input

2. **deploy.sh**: Handles the deployment process:
   - Creates a temporary copy of the Terraform files
   - Modifies them to work in a single-account setup
   - Configures the backend (local or S3)
   - Deploys the infrastructure
   - Extracts dashboard settings from Terraform configuration
   - Runs BATS tests to verify the deployment

3. **cleanup.sh**: Handles resource cleanup:
   - Empties and removes S3 buckets
   - Runs terraform destroy
   - Cleans up temporary files

## Prerequisites

- AWS CLI installed and configured with appropriate permissions
- Terraform >= 1.0 installed
- BATS (Bash Automated Testing System) installed
- jq installed for JSON processing
- QuickSight Enterprise subscription in your AWS account
- QuickSight user with appropriate permissions

## Setup Instructions

### 1. Configure AWS Credentials with Isengard

Before running the script, you must set up your AWS credentials from Isengard:

1. **Copy Isengard Temporary Credentials**:
   - Log into Isengard console and select the account you want to use
   - Expand bash/zsh, then click on "Copy bash/zsh"
   - Paste these credentials into your terminal to set the environment variables

2. **Configure AWS CLI Region**:
   - Ensure your AWS CLI is configured to use the correct region:
   ```bash
   aws configure set region eu-west-2  # Replace with your desired region
   ```
   - Verify your configuration:
   ```bash
   aws configure get region
   ```

3. **Verify IDE Access**:
   - Make sure your IDE has access to these environment variables
   - For VS Code, you may need to launch it from the terminal where you set the credentials
   - Verify access with:
   ```bash
   aws sts get-caller-identity
   ```

### 2. Create terraform.tfvars File

Create a `terraform.tfvars` file in the `terraform` directory with your configuration:

```hcl
global_values = {
  destination_account_id = "123456789012"      # Your AWS account ID
  source_account_ids     = "123456789012"      # Same account ID for local testing
  aws_region             = "eu-west-2"         # Your preferred region
  quicksight_user        = "your-username"     # Your QuickSight username
  cid_cfn_version        = "4.2.5"             # CID CloudFormation version
  data_export_version    = "0.5.0"             # Data Export version
  environment            = "dev"               # Environment (use "dev" for testing)
}
```

### 3. No Script Configuration Needed

The script automatically uses the values from your `terraform.tfvars` file, so no additional configuration is required in the script itself.

## Running the Tests

1. Make the scripts executable:
   ```bash
   chmod +x tf-test-local-run.sh deploy.sh cleanup.sh
   ```

2. Run the main script:
   ```bash
   ./tf-test-local-run.sh
   ```

3. Advanced usage with options:
   ```bash
   # Use S3 backend instead of local
   ./tf-test-local-run.sh --s3 --bucket your-bucket-name --region eu-west-2
   
   # Skip cleanup prompt
   ./tf-test-local-run.sh --skip-cleanup
   
   # Use custom resource prefix
   ./tf-test-local-run.sh --resource-prefix my-cid-test
   ```

4. The script will:
   - Process command-line arguments
   - Call deploy.sh to deploy the infrastructure and run tests
   - Display test results
   - Ask if you want to clean up resources (unless --skip-cleanup is used)
   - Call cleanup.sh if cleanup is requested

## BATS Tests

The `dashboards.bats` file contains tests that verify:

1. The dashboards exist in QuickSight
2. The required datasets exist
3. The Athena data source exists
4. The dashboard views are properly configured

## Cleanup

When prompted at the end of the script, enter `y` to clean up all resources. The cleanup process:

1. Empties S3 buckets (including versioned objects and delete markers)
2. Removes the buckets
3. Runs `terraform destroy` to remove:
   - CloudFormation stacks
   - IAM roles and policies
   - QuickSight resources
4. Cleans up temporary files

You can also run the cleanup script directly:
```bash
./cleanup.sh
```

Or with specific backend configuration:
```bash
BACKEND_TYPE=s3 S3_BUCKET=your-bucket S3_REGION=eu-west-2 ./cleanup.sh
```

## Troubleshooting

- **QuickSight Access**: Ensure your QuickSight user has Enterprise subscription and appropriate permissions
- **AWS Permissions**: Your AWS credentials must have permissions to create and manage all required resources
- **Region Issues**: Make sure the AWS_REGION in the script matches your terraform.tfvars configuration
- **Test Failures**: Check the test output log at `/tmp/cudos_test/test_output.log` for details
- **Version Detection**: The workflow extracts the CID version from the local cid-cfn.yml file by looking for the line containing "Cloud Intelligence Dashboards" in the Description field

## Notes

- By default, the scripts use a local Terraform state file stored in the `tfstate` directory
- You can switch to an S3 backend by using the `--s3` flag with appropriate bucket parameters
- The deployment script comments out the `cid_dataexports_source` resource to enable single-account deployment
- All modifications are made to a temporary copy of the Terraform files, preserving your original files
- The scripts automatically detect which dashboards are configured for deployment in your Terraform variables
- Resource prefix can be customized with the `--resource-prefix` flag (default: "cid-tf")
- The cleanup script handles versioned S3 buckets properly by removing all versions and delete markers