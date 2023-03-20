#!/bin/bats

# Run: bats ./terraform-modules/terraform-test.bats --timing
# Debug: bats ./terraform-modules/terraform-test.bats --timing --show-output-of-passing-tests

# Testing happy path of creating/deleting stack

# prereqs:
#   1. Quicksight Enterprise edition
#   2. Quicksight has rights to read all s3 buckets in the account (not managable today)
#   3. At least 1 CUR created

setup_file() {
  # Vars
  export stackname="tfstack$(date +%Y%m%d%H%M)"
  export account_id=$(aws sts get-caller-identity --query Account --output text)
  export quicksight_user=$(aws quicksight list-users --aws-account-id $account_id --namespace default --query 'UserList[0].UserName' --output text)
  export template_bucket=test-cid-tf-template-$account_id
  export cur_bucket=test-cid-tf-cur-$account_id

  aws quicksight describe-user --aws-account-id $account_id --user-name $quicksight_user --namespace default
  if [[ "$?" != "0" ]]; then
      echo "Missing QS User '$quicksight_user'"
      return 1
  fi

  export qs_edition=$(aws quicksight describe-account-settings --aws-account-id $account_id --query 'AccountSettings.Edition' --output text)
  if [[ "$qs_edition" != "ENTERPRISE" ]]; then
      echo "Missing ENTERPRISE edition in QuickSight"
      return 1
  fi

  # Create a tmp bucket to store CFN template
  if aws s3api head-bucket --bucket "$template_bucket" 2>/dev/null; then
    echo 'Template Bucket exist'
  else
    echo 'Creating bucket for template'
    aws s3api create-bucket --bucket $template_bucket
  fi

  # Create a tmp bucket for CUR
  if aws s3api head-bucket --bucket "$cur_bucket" 2>/dev/null; then
    echo 'CUR Bucket exist'
  else
    aws s3api create-bucket --bucket $cur_bucket
  fi

  # Create workspace
  export tf_workspace=$(mktemp -d .tftest.XXXXXX)
}


@test "generate terraform manifest" {
  export git_base_url=$(git config --get remote.origin.url | cut -d '@' -f2 | sed s/.git// | sed s@https://@@ | tr : /)
  export git_branch=$(git branch --show-current)

  # Create a tf file
  cat > "$tf_workspace/main.tf" <<EOL
  module "cid_dashboards" {
      source = "$git_base_url//terraform-modules/cid-dashboards?ref=$git_branch"
      stack_name       = "$stackname"
      template_bucket  = "$template_bucket"
      stack_parameters = {
        "PrerequisitesQuickSight"            = "yes"
        "PrerequisitesQuickSightPermissions" = "yes"
        "QuickSightUser"                     = "$quicksight_user"
        "DeployCUDOSDashboard"               = "yes"
        "DeployCostIntelligenceDashboard"    = "no"
        "DeployKPIDashboard"                 = "no"
        "CURBucketPath"                      = "s3://$cur_bucket/cur"
        "Suffix"                             = "-test-tf"
      }
  }
EOL
}

@test "terraform init" {
  terraform -chdir="$tf_workspace" init
}

@test "terraform apply (takes 5 mins)" {
  terraform -chdir="$tf_workspace" apply -auto-approve
  terraform -chdir="$tf_workspace" state list
}

@test "cloud formation stack is created successfully" {
  run aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE --query "length(StackSummaries[?StackName==\`$stackname\`])" --output text
  [ "$status" -eq 0 ]
  [ "$output" = "1" ]
}

@test "terraform destroy (takes 5 mins)" {
  terraform -chdir="$tf_workspace" destroy -auto-approve
}

@test "cloud formation stack is deleted" {
  run aws cloudformation list-stacks --stack-status-filter DELETE_COMPLETE --query "length(StackSummaries[?StackName==\`$stackname\`])" --output text
  [ "$status" -eq 0 ]
  [ "$output" = "1" ]
}

teardown_file() {
  # Additional teardown steps in case of failure
  export region=$(aws configure get region)
  aws s3 rm s3://aws-athena-query-results-cid-$account_id-$region --recursive || echo "no bucket"
  aws s3api delete-bucket --bucket aws-athena-query-results-cid-$account_id-$region || echo "no bucket"
  aws athena delete-work-group --work-group CID --recursive-delete-option

  # Normal cleanup
  aws s3 rm s3://$template_bucket/ --recursive
  aws s3api delete-bucket --bucket $template_bucket
  aws s3 rm s3://$cur_bucket/ --recursive
  aws s3api delete-bucket --bucket $cur_bucket
  rm -rf "$tf_workspace"
}