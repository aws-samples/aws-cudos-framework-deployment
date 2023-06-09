# CID Terraform Modules

We provide Terraform modules for your convenience in deploying CID dashboards.

## Module List

Currently, the following modules are provided:

### [cur-setup-source](./cur-setup-source/README.md)

Terraform module to set up a Cost and Usage Report in a source (payer) account
for use in Cost Intelligence Dashboards. The module creates an S3 bucket with
the necessary permissions and configuration to replicate CUR data to the
destination/aggregation account. If you are deploying Cost Intelligence Dashboards
for a multi-payer environment, you can deploy one instance of this module for
each payer account. 

Review [module documentation](./cur-setup-source/README.md) for details
on module requirements, inputs, and outputs.

### [cur-setup-destination](./cur-setup-destination/README.md)

Terraform module to set up a Cost and Usage Report in a destination/aggregation
account for use in Cost Intelligence Dashboards. The module creates an S3 bucket
with the necessary permissions for replicating CUR data from one or more source
accounts. If the aggregation account is part of a different payer and is not
covered in the CUR from the source accounts, the module can create a new Cost
and Usage Report local to the aggregation account.

Review [module documentation](./cur-setup-destination/README.md) for details
on module requirements, inputs, and outputs.

### [cid-dashboards](./cid-dashboards/README.md)

Terraform module to deploy CID dashboards. This module is a wrapper around
CloudFormation to allow you to deploy CID dashboards using your existing
Terraform workflows. Under the hood, the module will deploy a CloudFormation
stack which will provision the necessary resources and a custom Lambda
function to create the dashboards using `cid-cmd`.

Review [module documentation](./cid-dashboards/README.md) for details
on module requirements, inputs, and outputs.

## Module Usage

The modules provided are intended to be used as remote modules using
the GitHub / git source as below.

```hcl
module "example" {
  source = "github.com/aws-samples/aws-cudos-framework-deployment//terraform-modules/<module name>"
  ...
}
```

You can customize the modules using input variables and retrieve output values
from the module outputs.

### Version Locking

For production deployments, you should lock module versions to a release
tag to better control when and what updates are made. To specify the
release tag to use, append `?ref=VERSION` to the module source. For
example, the following source reference will use the Terraform module
and Cloudformation template from version 0.2.14 of this module:

```
source = "github.com/aws-samples/aws-cudos-framework-deployment//terraform-modules/cur-setup-source?ref=0.2.14"
```

For a complete list of release tags, visit https://github.com/aws-samples/aws-cudos-framework-deployment/tags.

*Note: The same syntax can be used to use pre-release/beta versions by
specifying a branch name instead of a tag name*

## Deployment Instructions

### Step 1: CUR Setup

If you have not set up CUR for use with CID dashboards, deploy the
[cur-setup-destination](./cur-setup-destination/README.md) module to your
data collection account. Then, in your payer account(s), deploy the
[cur-setup-source](./cur-setup-source/README.md) module. You can choose to
deploy both modules in a single Terraform root module/workspace

#### Example Usage

```hcl
# cur_setup.tf

provider "aws" {
  profile = "src"
  region  = "us-west-2"
  alias   = "src"
}

provider "aws" {
  profile = "src"
  region  = "us-east-1"
  alias   = "src_useast1"
}

provider "aws" {
  profile = "dst"
  region  = "us-west-2"
  alias   = "dst"
}

provider "aws" {
  profile = "dst"
  region  = "us-east-1"
  alias   = "dst_useast1"
}

# Configure exactly one destination account
module "cur_destination" {
  source = "github.com/aws-samples/aws-cudos-framework-deployment//terraform-modules/cur-setup-destination

  source_account_ids = ["1234567890"]
  create_cur         = false # Set to true to create an additional CUR in the aggregation account

  # Provider alias for us-east-1 must be passed explicitly (required for CUR setup)
  # Optionally, you may pass the default aws provider explicitly as well
  providers = {
    aws         = aws.dst
    aws.useast1 = aws.dst_useast1
  }
}

# Configure one or more source (payer) accounts
module "cur_source" {
  source = "github.com/aws-samples/aws-cudos-framework-deployment//terraform-modules/cur-setup-source"

  destination_bucket_arn = module.cur_destination.cur_bucket_arn

  # Provider alias for us-east-1 must be passed explicitly (required for CUR setup)
  # Optionally, you may pass the default aws provider explicitly as well
  providers = {
    aws         = aws.src
    aws.useast1 = aws.src_useast1
  }
}
```

### Step 2: Dashboard Prerequisite Setup

After enabling CUR, either manually or with Terraform as described above,
a few steps are necessary to prepare for dashboard deployment:
  1. Complete prerequisites in [Before You Start](../../README.md#before-you-start) including Quicksight setup
  2. Create an S3 bucket to upload the CloudFormation template

### Step 3: Dashboard Setup

In a separate Terraform root module/workspace, deploy the [cid-dashboards](./cur-setup-source/README.md) module to your data collection (destination) account.
Only deploy one instance of this module. To deploy multiple dashboards, customize
the `stack_parameters` to deploy the desired dashboards. Refer to the
[module documentation](./cur-setup-source/README.md) for the most frequently
used `stack_parameters`.


#### Example Usage

```hcl
# dashboard_deployment.tf

module "cid_dashboards" {
    source = "github.com/aws-samples/aws-cudos-framework-deployment//terraform-modules/cid-dashboards"

    stack_name       = "Cloud-Intelligence-Dashboards"
    template_bucket  = "UPDATEME" # Update with 
    stack_parameters = {
      "PrerequisitesQuickSight"            = "yes"
      "PrerequisitesQuickSightPermissions" = "yes"
      "QuickSightUser"                     = "UPDATEME"
      "DeployCUDOSDashboard"               = "yes"
      "DeployCostIntelligenceDashboard"    = "yes"
      "DeployKPIDashboard"                 = "yes"
    }
}
```

