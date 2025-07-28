# AWS Cloud Intelligence Dashboards (CID) Terraform Module

This Terraform module deploys the AWS Cloud Intelligence Dashboards (formerly CUDOS) infrastructure using CloudFormation stacks. It provides a streamlined way to set up cost management and optimization dashboards in your AWS environment.

## Architecture Overview

The module creates the following CloudFormation stacks across two AWS accounts:

1. **Data Exports Destination Stack** - Deployed in the Data Collection account to manage data aggregation
2. **Data Exports Source Stack** - Deployed in the Payer account to collect cost data
3. **Cloud Intelligence Dashboards Stack** - Deployed in the Data Collection account for QuickSight dashboards

This architecture follows AWS best practices by separating the Payer account (Source/Management account) from the dashboard visualization (Data Collection account). For a detailed architecture diagram, see the [CID Architecture Documentation](https://catalog.workshops.aws/awscid/en-US/dashboards/foundational/cudos-cid-kpi/deploy#architecture).

## Prerequisites

* Terraform >= 1.0
* Access to deploy resources in both accounts:

  * **Payer account**: Permissions to create IAM roles, S3 buckets, and access billing data
  * **Data Collection account**: Permissions to create CloudFormation stacks, S3 buckets, and manage QuickSight
* QuickSight Enterprise subscription in the Data Collection account
* A configured QuickSight user in the Data Collection account
* Terraform provider configuration for both accounts:

  * Default provider for the Payer account
  * Provider with "destination\_account" alias for the Data Collection account

## Quick Start

1. Call the Terraform module using the correct AWS providers:

```bash
module "cloud-intelligence-dashboard" {
  source = "github.com/aws-solutions-library-samples/cloud-intelligence-dashboards-framework//terraform/cicd-deployment?ref=<release-tag>"
  
  providers = {
    aws = aws.payer
    aws.destination = aws.destination
  }

  global_values = {
    destination_account_id = "123456789012"      # 12-digit Data Collection account ID
    source_account_ids     = "987654321098"      # Comma-separated list of Payer account IDs
    aws_region             = "us-east-1"         # AWS region for deployment
    quicksight_user        = "user/example"      # QuickSight username
    cid_cfn_version        = "4.2.7"             # CID CloudFormation version - Supporting from 4.2.7
    data_export_version    = "0.5.0"             # Data Export version
    environment            = "dev"               # Environment (dev, staging, prod)
  }

}

provider "aws" {
  alias  = "payer" # optional
  region = <region>
  assume_role { # optional
    role_arn = <payer iam role (if required)>
  }
}
 
provider "aws" {
  alias  = "destination_account"
  region = <region>
  assume_role { # optional
    role_arn = <destination iam role (if required)>
  }
}
```

2. Configure AWS credentials for both accounts, or use credentials capable of assuming the IAM role defined in the provider(s).
3. Run the standard Terraform workflow:

```bash
terraform init
terraform plan
terraform apply
```

## Configuration

### Required Variables

The module expects the following input variables:

```hcl
global_values = {
  destination_account_id = "123456789012"      # 12-digit Data Collection account ID
  source_account_ids     = "987654321098"      # Comma-separated list of Payer account IDs
  aws_region             = "us-east-1"         # AWS region for deployment
  quicksight_user        = "user/example"      # QuickSight username
  cid_cfn_version        = "4.2.7"             # CID CloudFormation version - Supporting from 4.2.7
  data_export_version    = "0.5.0"             # Data Export version
  environment            = "dev"               # Environment (dev, staging, prod)
}
```

> **Note:** To get the latest version numbers for `cid_cfn_version` and `data_export_version`, you can use the following commands:
>
> ```bash
> CID_VERSION=$(curl -s https://raw.githubusercontent.com/aws-solutions-library-samples/cloud-intelligence-dashboards-framework/main/cfn-templates/cid-cfn.yml | grep Description | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)
> echo "cid_cfn_version = \"$CID_VERSION\""
>
> EXPORT_VERSION=$(curl -s https://raw.githubusercontent.com/aws-solutions-library-samples/cloud-intelligence-dashboards-data-collection/main/data-exports/deploy/data-exports-aggregation.yaml | grep Description | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)
> echo "data_export_version = \"$EXPORT_VERSION\""
> ```

### Optional Configuration

The module includes sensible defaults for all other parameters. You can override them in your `terraform.tfvars` file as needed:

```hcl
# Data Exports Destination Configuration (Data Collection account)
cid_dataexports_destination = {
  resource_prefix  = "cid"
  manage_cur2      = "yes"
  manage_focus     = "no"
  manage_coh       = "no"
  enable_scad      = "yes"
  role_path        = "/"
  time_granularity = "HOURLY"
}

# Data Exports Source Configuration (Payer account)
cid_dataexports_source = {
  source_resource_prefix  = "cid"
  source_manage_cur2      = "yes"
  source_manage_focus     = "no"
  source_manage_coh       = "no"
  source_enable_scad      = "yes"
  source_role_path        = "/"
  source_time_granularity = "HOURLY"
}

# Dashboard Configuration (Data Collection account)
cloud_intelligence_dashboards = {
  # Dashboard Selection
  deploy_cudos_v5                    = "yes"
  deploy_cost_intelligence_dashboard = "yes"
  deploy_kpi_dashboard               = "yes"
  deploy_tao_dashboard               = "no"
  deploy_compute_optimizer_dashboard = "no"

  # Other configurations available - see variables.tf for all options
}
```

## Important Technical Parameters (Do Not Modify)

The following parameters are managed internally by the CID deployment and **must not be changed**. Modifying these may lead to deployment failure or broken dashboards:

| Parameter                     | Purpose                                    |
| ----------------------------- | ------------------------------------------ |
| `athena_workgroup`            | Used by Athena to run queries              |
| `athena_query_results_bucket` | Stores Athena query results for QuickSight |
| `database_name`               | Athena/Glue database used by dashboards    |
| `cur_table_name`              | Name of the legacy CUR table if applicable |
| `suffix`                      | Unique stack identifier                    |
| `lambda_layer_bucket_prefix`  | Bucket prefix for Lambda layers            |
| `deployment_type`             | Deployment mechanism (Terraform/CFN)       |

These values are mapped to CloudFormation parameters grouped under **"Technical Parameters. Please do not change."** and are only overridden internally by Terraform.

## Cross-Account Setup

This module implements a cross-account architecture:

1. **Payer Account**: Contains the billing data and CUR reports

   * Deploys the Data Exports Source stack
   * Creates IAM roles for cross-account access
   * Sets up S3 bucket policies for data sharing

2. **Data Collection Account**: Contains the dashboards and visualization

   * Deploys the Data Exports Destination stack
   * Deploys the Cloud Intelligence Dashboards stack
   * Hosts the QuickSight dashboards and datasets

The cross-account setup ensures proper separation of concerns and follows AWS security best practices.

## Available Dashboards

The module can deploy the following dashboards in the Data Collection account:

| Dashboard         | Variable                             | Default |
| ----------------- | ------------------------------------ | ------- |
| CUDOS v5          | `deploy_cudos_v5`                    | yes     |
| Cost Intelligence | `deploy_cost_intelligence_dashboard` | yes     |
| KPI               | `deploy_kpi_dashboard`               | yes     |
| TAO               | `deploy_tao_dashboard`               | no      |
| Compute Optimizer | `deploy_compute_optimizer_dashboard` | no      |

## Outputs

After successful deployment, the module provides the following outputs:

| Output                                  | Description                    |
| --------------------------------------- | ------------------------------ |
| `cid_dataexports_destination_outputs`   | Outputs from destination stack |
| `cid_dataexports_source_outputs`        | Outputs from source stack      |
| `cloud_intelligence_dashboards_outputs` | QuickSight dashboard outputs   |

Access the dashboard URLs from the outputs to view your dashboards in QuickSight.

## Important Notes

* Stack creation can take up to 60 minutes
* All stacks require `CAPABILITY_IAM` and `CAPABILITY_NAMED_IAM` permissions
* The module uses S3 for Terraform state storage
* QuickSight Enterprise subscription is required in the Data Collection account
* Cross-account IAM roles are created automatically

## Customization

### Provider Configuration

The module needs access to both the payer/master and destination accounts to deploy CloudFormation stacks. The configuration below shows a sample providers setup:

```hcl
provider "aws" {
  alias  = "payer" # optional
  region = <region>
  assume_role { # optional
    role_arn = <payer iam role (if required)>
  }
}
 
provider "aws" {
  alias  = "destination_account"
  region = <region>
  assume_role { # optional
    role_arn = <destination iam role (if required)>
  }
}
```

## Resource Details

### Data Exports Source Stack

* Deployed in the Payer account
* Creates IAM roles for cross-account access
* Sets up CUR report configuration
* Configures S3 bucket policies for data sharing

### Data Exports Destination Stack

* Deployed in the Data Collection account
* Creates S3 buckets for data collection
* Sets up Athena database and tables
* Configures IAM roles and policies
* Manages CUR, FOCUS, and COH data as configured

### Cloud Intelligence Dashboards Stack

* Deployed in the Data Collection account
* Deploys selected QuickSight dashboards
* Configures data sources and datasets
* Sets up necessary IAM permissions
* Creates dashboard sharing as configured

## Timeouts

All CloudFormation stacks are configured with 60-minute timeouts for create, update, and delete operations.

## FAQ

<details>
<summary><b>How do I backfill historical cost data?</b></summary>

To backfill historical data for the Data Export, follow the instructions in the [CID Workshop Backfill Data Export section](https://catalog.workshops.aws/awscid/en-US/dashboards/foundational/cudos-cid-kpi/deploy#backfill-data-export).

This process allows you to populate your dashboards with historical cost and usage data, ensuring you have a complete view of your AWS spending over time.

</details>

<details>
<summary><b>Can I deploy everything in a single account instead of using cross-account setup?</b></summary>

The module is configured by default for cross-account deployment, which is recommended for production environments. 
If you prefer to deploy in a single account, you can deploy the entire solution within your payer account, without the need for a separate data collection account.
This single-account setup is simpler and better suited for testing or development purposes.

1. **Modify main.tf**:
   * Comment out or remove the `resource "aws_cloudformation_stack" "cid_dataexports_source"` block
   * Update any dependencies that reference this resource

2. **Modify outputs.tf**:
   * Remove or comment out the `output "cid_dataexports_source_outputs"` block

3. **Remove the variable**:
   * Remove or comment out the `cid_dataexports_source` variable block

4. **Create terraform.tfvars**:

   ```hcl
   global_values = {
     destination_account_id = "123456789012"      # Your Payer account ID
     source_account_ids     = "123456789012"      # Same Payer account ID
     aws_region             = "us-east-1"         # AWS region for deployment
     quicksight_user        = "user/example"      # QuickSight username
     cid_cfn_version        = "4.2.5"             # CID CloudFormation version
     data_export_version    = "0.5.0"             # Data Export version
     environment            = "dev"               # Environment (dev, staging, prod)
   }
   ```

5. **Simplify provider.tf**:

   ```hcl
  provider "aws" {
    region = <region>
    assume_role { # optional
      role_arn = <payer iam role (if required)>
    }
  }
  
  provider "aws" {
    alias  = "destination_account"
    region = <region>
    assume_role { # optional
      role_arn = <same payer iam role (if required)>
    }
  }
   ```

This configuration will deploy only the Data Exports Destination Stack and the Cloud Intelligence Dashboards Stack directly in your Payer account, skipping the separate Source Stack that would normally be deployed in a cross-account setup.

> **Note:** Single-account deployment in your Payer account is simpler for testing but lacks the security benefits and separation of concerns provided by the recommended cross-account architecture. For production environments, we strongly recommend the cross-account approach. For more details on the recommended architecture, see the [CID Architecture Documentation](https://catalog.workshops.aws/awscid/en-US/dashboards/foundational/cudos-cid-kpi/deploy#architecture).

</details>

<details>
<summary><b>Is there an automated tool for single-account deployment?</b></summary>

Yes, we provide a testing framework in the `terraform-test` directory that simplifies single-account deployment for testing purposes. This framework includes scripts that automatically handle the necessary modifications to deploy everything in a single account.

For detailed instructions on using this testing framework, refer to the [README.md in the terraform-test directory](../terraform-test/README.md). The testing framework:

1. Automatically comments out the source stack resource
2. Configures the proper account IDs
3. Sets up the appropriate provider configuration
4. Provides options for local or S3 backend configuration

This is the recommended approach for testing and development environments when you want to use a single account.

</details>

## Additional Resources

* [AWS Cloud Intelligence Dashboards Documentation](https://catalog.workshops.aws/awscid/en-US)
* [Foundational Dashboards Deployment Workshop](https://catalog.workshops.aws/awscid/en-US/dashboards/foundational)
* [QuickSight Documentation](https://docs.aws.amazon.com/quicksight/latest/user/welcome.html)
