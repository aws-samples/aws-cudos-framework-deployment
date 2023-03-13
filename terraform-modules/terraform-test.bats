#!/bin/bats

# This is a Bats test file. See https://bats-core.readthedocs.io

# Run:
#   bats $thisfile

# Debug:
#   bats $thisfile --show-output-of-passing-tests

@test "setup environment" {

  #Vars
  export account_id=$(aws sts get-caller-identity --query Account --output text)
  export qs_username=$(aws quicksight list-users --aws-account-id $account_id --namespace default --query 'UserList[0].UserName' --output text)
  export template_bucket=test-cid-tf-template-$account_id
  export cur_bucket=test-cid-tf-cur-$account_id

  # Create a tmp bucket to store CFN template
  if aws s3api head-bucket --bucket "$template_bucket" 2>/dev/null; then
    echo 'Template Bucket exist'
  else
    echo 'Creating bucket for template'
    aws s3api create-bucket --bucket $template_bucket
  fi

  # Create a tmp bucket to store CFN template
  if aws s3api head-bucket --bucket "$cur_bucket" 2>/dev/null; then
    echo 'CUR Bucket exist'
  else
    aws s3api create-bucket --bucket $cur_bucket
  fi

}


@test "generate terraform manifest" {

  export git_base_url=$(git config --get remote.origin.url | cut -d '@' -f2 | sed s/.git// | sed s@https://@@ | tr : /)
  export git_branch=$(git branch --show-current)

  # Create a tf file
  cat >main.tf <<EOL
  module "cid_dashboards" {
      source = "$git_base_url//terraform-modules/cid-dashboards?ref=$git_branch"
      stack_name       = "CIDDashboards"
      template_bucket  = "$template_bucket"
      stack_parameters = {
        "PrerequisitesQuickSight"            = "yes"
        "PrerequisitesQuickSightPermissions" = "yes"
        "QuickSightUser"                     = "$qs_username"
        "DeployCUDOSDashboard"               = "yes"
        "DeployCostIntelligenceDashboard"    = "no"
        "DeployKPIDashboard"                 = "no"
        "CURBucketPath"                      = "s3://$cur_bucket/cur"
        "Suffix"                             = "test-tf-"
      }
  }
EOL

}

@test "terraform init" {
  terraform init
}

@test "terraform plan" {
  terraform plan
}

@test "terraform apply (takes 5 mins)" {
  terraform apply -auto-approve
  terraform state list
}

@test "cloud formation stack is created" {
  skip 'todo'
}

@test "terraform destroy " {
  terraform destroy -auto-approve
}

@test "cloud formation stack is deleted" {
  skip 'todo'
}

teardown_file() {
  #Additional teardown steps in case of failure
  export region=$(aws configure get region)
  aws s3 rm s3://aws-athena-query-results-cid-$account_id-$region --recursive || echo "no bucket"
  aws s3api delete-bucket --bucket aws-athena-query-results-cid-$account_id-$region || echo "no bucket"
  aws athena delete-work-group --work-group CID --recursive-delete-option

  # Normal cleanup
  aws s3 rm s3://$template_bucket/ --recursive
  aws s3api delete-bucket --bucket $template_bucket

  aws s3 rm s3://$cur_bucket/ --recursive
  aws s3api delete-bucket --bucket $cur_bucket

}