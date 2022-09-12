
# Testing happy path of creating/deleting stack

# prereqs:
#   1. Quicksight Enterprise edition
#   2. Quicksight has rights to read all s3 bukets in the account (not managable today)
#   3. at least 1 CUR created

setup() {
  export stackname="stack$(date +%Y%m%d%H%M)"
  export account_id=$(aws sts get-caller-identity --query Account --output text)
  export cid_version=$(python3 -c 'from cid._version import __version__;print(__version__)')
  export quicksight_user=$(aws sts get-caller-identity --query Arn --output text| cut -d/ -f2-)

  aws quicksight describe-user --aws-account-id $account_id --user-name $quicksight_user --namespace default
  if [[ "$?" != "0" ]]; then
      echo "Missing CUR"
      return 1
  fi

  export cur_name=$(aws cur describe-report-definitions --query 'ReportDefinitions[0].ReportName' --output text)
  export cur_bucket=$(aws cur describe-report-definitions --query 'ReportDefinitions[0].S3Bucket' --output text)
  export cur_prefix=$(aws cur describe-report-definitions --query 'ReportDefinitions[0].S3Prefix' --output text)
  if [[ "$?" != "0" ]]; then
      echo "Missing CUR"
      return 1
  fi

  export qs_edition=$(aws quicksight describe-account-settings --aws-account-id $account_id --query 'AccountSettings.Edition' --output text)
  if [[ "$qs_edition" != "ENTERPRISE" ]]; then
      echo "Missing ENTERPRISE edition in QuickSight"
      return 1
  fi
}


@test "Prereqs: QS has ENTERPRISE edition" {
  run aws quicksight describe-account-settings --aws-account-id $account_id --query 'AccountSettings.Edition' --output text
  [ "$status" -eq 0 ]
  [ "$output" = "ENTERPRISE" ]
}

@test "Prereqs: CUR created" {
  [ "$cur_name" != "" ]
}

@test "Prereqs: QS has permissions to read buckets" {
  skip 'not implemented'
  #FIXME: need to check policies. Can start from here, but this list is empty.
  aws iam list-role-policies --role-name aws-quicksight-service-role-v0
}
@test "install stack (5 mins)" {
  aws cloudformation deploy \
  --template-file  ./cfn-templates/cid-cfn.yml \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM  \
  --parameter-overrides \
      PrerequisitesCUR="yes"\
      PrerequisitesQuickSight="yes"\
      PrerequisitesQuickSightPermissions="yes"\
      QuickSightUser="$quicksight_user"\
      CURBucketPath="s3://$cur_bucket/$cur_prefix/$cur_name/$cur_name"\
      CostOptimizationDataCollectionBucketPath="s3://costoptimizationdata{account_id}"\
      DeployCUDOSDashboard="yes"\
      DeployComputeOptimizerDashboard="no"\
      DeployCostIntelligenceDashboard="yes"\
      DeployKPIDashboard="yes"\
      DeployTAODashboard="no"\
      AthenaWorkgroup=""\
      AthenaQueryResultsBucket=""\
      CURDatabaseName=""\
      CURPath=""\
      CURTableName=""\
      CidVersion="$cid_version"\
      QuickSightDataSetRefreshSchedule="cron(0 4 * * ? *)"\
      QuicksightIdentityRegion="us-east-1"\
      Suffix=""\
    --stack-name "$stackname"

  aws cloudformation wait stack-create-complete \
    --stack-name "$stackname"
}

@test "Workrgroup created" {
  run aws athena list-work-groups --query 'length(WorkGroups[?Name==`CID`])' --output text
  [ "$status" -eq 0 ]
  [ "$output" = "1" ]
}

@test "CUDOS created succesfuly" {
  run aws quicksight describe-dashboard --dashboard-id cudos --aws-account-id $account_id --query 'Dashboard.Version.Status' --output text
  [ "$status" -eq 0 ]
  [ "$output" = "CREATION_SUCCESSFUL" ]
}

@test "COD not installed" {
  run aws quicksight describe-dashboard --dashboard-id compute-optimization-dashboard --aws-account-id $account_id --query 'Dashboard.Version.Status' --output text
  [ "$status" -ne 0 ]
}

@test "Delete stack (5 mins)" {
  export stackname=$(aws cloudformation describe-stacks --query 'Stacks[?Description==`Deployment of Cloud Intelligence Dashboards`].StackName' --output text)
  aws cloudformation delete-stack --stack-name "$stackname"
  aws cloudformation wait stack-delete-complete  --stack-name "$stackname"

  # Additional teardown steps in case of failure
  # aws s3 rm s3://aws-athena-query-results-cid-$account_id-$region --recursive
  # aws s3api delete-bucket --bucket aws-athena-query-results-cid-$account_id-$region
}

@test "Dashboards are deleted" {
  run aws quicksight list-dashboards --aws-account-id $account_id --query 'length(DashboardSummaryList)' --output text
  [ "$status" -eq 0 ]
  [ "$output" = "0" ]
}

@test "Datasets are deleted" {
  run aws quicksight list-data-sets --aws-account-id $account_id --query 'length(DataSetSummaries)' --output text
  [ "$status" -eq 0 ]
  [ "$output" = "0" ]
}

@test "DataSources are deleted" {
  run aws quicksight list-data-sources --aws-account-id $account_id --query 'length(DataSources[?Name==`CID-Athena`].Name)' --output text
  [ "$status" -eq 0 ]
  [ "$output" = "0" ]
}

@test "Workrgroups are deleted" {
  run aws athena list-work-groups --query 'length(WorkGroups[?Name==`CID`])' --output text
  [ "$status" -eq 0 ]
  [ "$output" = "0" ]
}


