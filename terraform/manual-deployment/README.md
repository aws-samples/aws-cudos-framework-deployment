# CUDOS Dashboard Manual Deployment

This Terraform configuration deploys the AWS Cost Intelligence Dashboards (CUDOS) infrastructure using CloudFormation stacks. The configuration sets up data exports and dashboards for cost management and optimization.

## Deployment Overview

The deployment consists of three separate steps, each with its own Terraform configuration:

1. cur-setup-destination (Data Collection Account)
2. cur-setup-destination (Payer Account)
3. cid-dashboard (Data Collection Account)

## Prerequisites

- AWS account with appropriate permissions
- Terraform installed
- AWS provider configured
- Required variables defined in a terraform.tfvars file

## Stack Details

### 1. Data Exports Child Stack
Creates a Cloudformation stack for data exports aggregation with the following features:
- Deployed in the destination account
- Manages CUR, FOCUS, and COH data
- Configurable resource prefix and time granularity
- IAM capabilities enabled

### 2. Data Exports Management Stack
Creates a Cloudformation stack for data exports with:
- Dependencies on the child stack
- Similar configuration options as the child stack
- Management-specific resource prefixes
- IAM capabilities enabled

### 3. CUDOS Dashboard Stack
Deploys the main CUDOS dashboard with:
- QuickSight integration
- Multiple dashboard deployment options
- Cost and Usage Report (CUR) configuration
- Optimization features
- Technical configurations for Athena and Lake Formation

## Configuration Parameters

### Global Parameters
- `destination_account_id`: Target AWS account ID
- `source_account_ids`: List of source AWS account IDs
- `quicksight_user`: QuickSight username

### Dashboard-specific Parameters
- CUR Configuration
- Optimization Settings
- Technical Settings
- QuickSight Prerequisites

## Usage

1. Configure the required variables in your terraform.tfvars file
2. Initialize Terraform:
```bash
terraform init
```
3. Review the planned changes:
```bash
terraform plan
```
4. Apply the configuration:
```bash
terraform apply
```


## Important Notes

### Permissions
- The configuration requires both `CAPABILITY_IAM` and `CAPABILITY_NAMED_IAM` permissions

### Deployment Time
- Stack creation and updates may take up to 60 minutes

### Integrations
- SNS topic integration is skipped as per checkov exception

### Prerequisites
- Ensure all required variables are properly set before deployment

## Dependencies

The stacks have the following hierarchical dependencies:

➤ CUDOS Dashboard
   ↳ Data Exports Management
   ↳ Data Exports Child

Stack Creation Order:
1. Data Exports Child
2. Data Exports Management
3. CUDOS Dashboard



- Data Exports Management depends on Data Exports Child
- CUDOS Dashboard depends on both Data Exports Management and Child stacks

## Timeouts

All stacks are configured with the following timeout settings:

| Operation | Duration |
|-----------|----------|
| Create    | 60 minutes |
| Update    | 60 minutes |
| Delete    | 60 minutes |

## Variables Configuration

### Data Exports Child Account Settings

| Variable | Type | Default | Description | Validation |
|----------|------|---------|-------------|------------|
| resource_prefix | string | "cid" | Prefix used for all named resources | Must match pattern ^[a-z0-9]+[a-z0-9-]{1,61}[a-z0-9]+$ |
| manage_cur2 | string | "yes" | Enable CUR 2.0 management | Must be "yes" or "no" |
| manage_focus | string | "no" | Enable FOCUS management | Must be "yes" or "no" |
| manage_coh | string | "no" | Enable Cost Optimization Hub management | Must be "yes" or "no" |
| enable_scad | string | "yes" | Enable Split Cost Allocation Data | Must be "yes" or "no" |
| role_path | string | "/" | Path for IAM roles | - |
| time_granularity | string | "HOURLY" | Time granularity for CUR 2.0 | Must be "HOURLY", "DAILY", or "MONTHLY" |

### Data Exports Management Account Settings

| Variable | Type | Default | Description | Validation |
|----------|------|---------|-------------|------------|
| mgmt_resource_prefix | string | "cid" | Prefix for management account resources | Must match pattern ^[a-z0-9]+[a-z0-9-]{1,61}[a-z0-9]+$ |
| mgmt_manage_cur2 | string | "yes" | Enable CUR 2.0 in management account | Must be "yes" or "no" |
| mgmt_manage_focus | string | "no" | Enable FOCUS in management account | Must be "yes" or "no" |
| mgmt_manage_coh | string | "no" | Enable Cost Optimization Hub in management account | Must be "yes" or "no" |
| mgmt_enable_scad | string | "yes" | Enable Split Cost Allocation Data in management account | Must be "yes" or "no" |
| mgmt_role_path | string | "/" | Path for IAM roles in management account | - |
| mgmt_time_granularity | string | "HOURLY" | Time granularity for CUR 2.0 in management account | Must be "HOURLY", "DAILY", or "MONTHLY" |

### CUDOS Dashboard Configuration

#### Prerequisites Variables
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| prerequisites_quicksight | string | "yes" | Enable QuickSight prerequisites |
| prerequisites_quicksight_permissions | string | "yes" | Enable QuickSight permissions |
| lake_formation_enabled | string | "no" | Enable Lake Formation |

#### CUR Parameters
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| cur_version | string | "2.0" | CUR version |
| deploy_cudos_v5 | string | "yes" | Deploy CUDOS v5 |
| deploy_cost_intelligence_dashboard | string | "yes" | Deploy Cost Intelligence Dashboard |
| deploy_kpi_dashboard | string | "yes" | Deploy KPI Dashboard |

#### Optimization Parameters
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| optimization_data_collection_bucket_path | string | "s3://cid-data-{account_id}" | S3 bucket path for optimization data |
| deploy_tao_dashboard | string | "no" | Deploy TAO Dashboard |
| deploy_compute_optimizer_dashboard | string | "no" | Deploy Compute Optimizer Dashboard |
| primary_tag_name | string | "owner" | Primary tag for resource tracking |
| secondary_tag_name | string | "environment" | Secondary tag for resource tracking |

#### Technical Parameters
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| athena_workgroup | string | "" | Athena workgroup name |
| athena_query_results_bucket | string | "" | S3 bucket for Athena query results |
| database_name | string | "" | Database name |
| glue_data_catalog | string | "AwsDataCatalog" | Glue data catalog name |
| suffix | string | "" | Resource name suffix |
| quicksight_data_source_role_name | string | "CidQuickSightDataSourceRole" | QuickSight data source IAM role |
| quicksight_data_set_refresh_schedule | string | "" | QuickSight refresh schedule |
| lambda_layer_bucket_prefix | string | "aws-managed-cost-intelligence-dashboards" | Lambda layer S3 bucket prefix |
| deploy_cudos_dashboard | string | "no" | Deploy CUDOS dashboard |
| data_buckets_kms_keys_arns | string | "" | KMS key ARNs for data buckets |
| share_dashboard | string | "yes" | Enable dashboard sharing |

#### Legacy Parameters
| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| keep_legacy_cur_table | string | "no" | Maintain legacy CUR table |
| cur_bucket_path | string | "s3://cid-{account_id}-shared/cur/" | CUR S3 bucket path |
| cur_table_name | string | "" | CUR table name |
| permissions_boundary | string | "" | IAM permissions boundary |
| role_path | string | "/" | IAM role path |

### Global Values Configuration

| Variable | Type | Default | Validation | Description |
|----------|------|---------|------------|-------------|
| destination_account_id | string | null | Must be 12 digits | AWS Account ID for DataExport replication |
| source_account_ids | string | "" | Must be comma-separated 12-digit IDs | Source AWS account IDs |
| aws_region | string | "" | - | AWS region for dashboard deployment |
| quicksight_user | string | null | Required | QuickSight user for dashboard sharing |


### Example Usage

```hcl
  data_exports_child = {
    resource_prefix  = "myprefix"
    manage_cur2      = "yes"
    manage_focus     = "yes"
    manage_coh       = "yes"
    enable_scad      = "yes"
    role_path        = "/"
    time_granularity = "HOURLY"
  }

  data_exports_management = {
    mgmt_resource_prefix  = "mgmt-prefix"
    mgmt_manage_cur2      = "yes"
    mgmt_manage_focus     = "no"
    mgmt_manage_coh       = "yes"
    mgmt_enable_scad      = "yes"
    mgmt_role_path        = "/"
    mgmt_time_granularity = "HOURLY"
  }

  cudos_dashboard            = {
    prerequisites_quicksight = "yes"
    deploy_cudos_v5          = "yes"
    primary_tag_name         = "department"
    secondary_tag_name       = "project"
    # ... other configurations
  }

  global_values            = {
    destination_account_id = "123456789012"
    source_account_ids     = "123456789012,987654321098"
    aws_region             = "us-east-1"
    quicksight_user        = "user@example.com"
  }
```
## Validation Rules
- Destination account ID must be exactly 12 digits
- Source account IDs must be comma-separated 12-digit numbers
- QuickSight user is required and cannot be null
- Most boolean flags use "yes"/"no" string values

## CloudFormation Stack Outputs

The following outputs are available from the CloudFormation stack:

### AggregateBucketName
- **Description**: Bucket with aggregate Data Exports
- **Value**: `${ResourcePrefix}-${DestinationAccountId}-data-exports`
- **Export Name**: `cid-DataExports-Bucket`

### Database
- **Description**: Database for Data Exports
- **Value**: `${ResourcePrefix}_data_export` (Note: hyphens are replaced with underscores)
- **Export Name**: `cid-DataExports-Database`

### LocalAccountBucket
- **Description**: Local Bucket Name which replicate objects to centralized bucket
- **Value**: `${ResourcePrefix}-${AWS::AccountId}-data-local`
- **Condition**: `DeployDataExport`

### ReadAccessPolicyARN
- **Description**: Policy to allow read access DataExports in S3 and Athena. Attach it to QuickSight role.
- **Value**: Reference to `DataExportsReadAccess`
- **Export Name**: `cid-DataExports-ReadAccessPolicyARN`
- **Condition**: `DeployAnyTable`

### Raw Template
```yaml
Outputs:
  AggregateBucketName:
    Description: Bucket with aggregate Data Exports
    Value: !Sub ${ResourcePrefix}-${DestinationAccountId}-data-exports
    Export: { Name: 'cid-DataExports-Bucket'}
  Database:
    Description: Database for Data Exports
    Value: !Join [ '_', !Split [ '-', !Sub '${ResourcePrefix}_data_export' ] ]
    Export: { Name: 'cid-DataExports-Database'}
  LocalAccountBucket:
    Condition: DeployDataExport
    Description: Local Bucket Name which replicate objects to centralized bucket
    Value: !Sub ${ResourcePrefix}-${AWS::AccountId}-data-local
  ReadAccessPolicyARN:
    Condition: DeployAnyTable
    Description: Policy to allow read access DataExports in S3 and Athena. Attach it to QuickSight role.
    Value: !Ref DataExportsReadAccess
    Export: { Name: 'cid-DataExports-ReadAccessPolicyARN'}
``` 
  

### Data Export Outputs

#### AggregateBucketName
- **Description**: Bucket with aggregate Data Exports
- **Value**: `${ResourcePrefix}-${DestinationAccountId}-data-exports`
- **Export Name**: `cid-DataExports-Bucket`

#### Database
- **Description**: Database for Data Exports
- **Value**: `${ResourcePrefix}_data_export` (Note: hyphens are replaced with underscores)
- **Export Name**: `cid-DataExports-Database`

#### LocalAccountBucket
- **Description**: Local Bucket Name which replicate objects to centralized bucket
- **Value**: `${ResourcePrefix}-${AWS::AccountId}-data-local`
- **Condition**: `DeployDataExport`

#### ReadAccessPolicyARN
- **Description**: Policy to allow read access DataExports in S3 and Athena. Attach it to QuickSight role.
- **Value**: Reference to `DataExportsReadAccess`
- **Export Name**: `cid-DataExports-ReadAccessPolicyARN`
- **Condition**: `DeployAnyTable`

### Dashboard URLs

#### CostIntelligenceDashboardURL
- **Description**: URL of CostIntelligenceDashboard
- **Value**: `CostIntelligenceDashboard.DashboardURL`
- **Condition**: `NeedCostIntelligenceDashboard`

#### CUDOSDashboardURL
- **Description**: URL of CUDOSDashboard
- **Value**: `CUDOSDashboard.DashboardURL`
- **Condition**: `NeedCUDOSDashboard`

#### CUDOSv5DashboardURL
- **Description**: URL of CUDOS Dashboard v5
- **Value**: `CUDOSv5Dashboard.DashboardURL`
- **Condition**: `NeedCUDOSv5`

#### KPIDashboardURL
- **Description**: URL of KPIDashboard
- **Value**: `KPIDashboard.DashboardURL`
- **Condition**: `NeedKPIDashboard`

#### TAODashboardURL
- **Description**: URL of TAODashboard
- **Value**: `TAODashboard.DashboardURL`
- **Condition**: `NeedTAODashboard`

#### ComputeOptimizerDashboardURL
- **Description**: URL of ComputeOptimizerDashboard
- **Value**: `ComputeOptimizerDashboard.DashboardURL`
- **Condition**: `NeedComputeOptimizerDashboard`

#### CidExecArn
- **Description**: Technical Value - CidExecArn
- **Value**: `CidExec.Arn`
- **Export Name**: `cid${Suffix}-CidExecArn`

### Raw Template
```yaml
Outputs:
  AggregateBucketName:
    Description: Bucket with aggregate Data Exports
    Value: !Sub ${ResourcePrefix}-${DestinationAccountId}-data-exports
    Export: { Name: 'cid-DataExports-Bucket'}
  Database:
    Description: Database for Data Exports
    Value: !Join [ '_', !Split [ '-', !Sub '${ResourcePrefix}_data_export' ] ]
    Export: { Name: 'cid-DataExports-Database'}
  LocalAccountBucket:
    Condition: DeployDataExport
    Description: Local Bucket Name which replicate objects to centralized bucket
    Value: !Sub ${ResourcePrefix}-${AWS::AccountId}-data-local
  ReadAccessPolicyARN:
    Condition: DeployAnyTable
    Description: Policy to allow read access DataExports in S3 and Athena. Attach it to QuickSight role.
    Value: !Ref DataExportsReadAccess
    Export: { Name: 'cid-DataExports-ReadAccessPolicyARN'}
  CostIntelligenceDashboardURL:
    Description: "URL of CostIntelligenceDashboard"
    Condition: NeedCostIntelligenceDashboard
    Value: !GetAtt CostIntelligenceDashboard.DashboardURL
  CUDOSDashboardURL:
    Description: "URL of CUDOSDashboard"
    Condition: NeedCUDOSDashboard
    Value: !GetAtt CUDOSDashboard.DashboardURL
  CUDOSv5DashboardURL:
    Description: "URL of CUDOS Dashboard v5"
    Condition: NeedCUDOSv5
    Value: !GetAtt CUDOSv5Dashboard.DashboardURL
  KPIDashboardURL:
    Description: "URL of KPIDashboard"
    Condition: NeedKPIDashboard
    Value: !GetAtt KPIDashboard.DashboardURL
  TAODashboardURL:
    Description: "URL of TAODashboard"
    Condition: NeedTAODashboard
    Value: !GetAtt TAODashboard.DashboardURL
  ComputeOptimizerDashboardURL:
    Description: "URL of ComputeOptimizerDashboard"
    Condition: NeedComputeOptimizerDashboard
    Value: !GetAtt ComputeOptimizerDashboard.DashboardURL
  CidExecArn:
    Description: Technical Value - CidExecArn
    Value: !GetAtt CidExec.Arn
    Export: { Name: !Sub 'cid${Suffix}-CidExecArn'}
```
