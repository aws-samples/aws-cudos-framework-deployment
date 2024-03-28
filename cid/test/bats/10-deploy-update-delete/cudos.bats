#!/bin/bats


account_id=$(aws sts get-caller-identity --query "Account" --output text )
database_name="${database_name:-athenacurcfn_cur1}" # If variable not set or null, use default
quicksight_user="${quicksight_user:-cicd-staging}" # If variable not set or null, use default
quicksight_datasource_id="${quicksight_datasource_id:-31c87a3c-8494-4f42-a590-c6930602e8e7}" # If variable not set or null, use default
cur_table="${cur_table:-cur1}" # If variable not set or null, use default. FIXME can be autodetected!


@test "Install" {
  run cid-cmd -vv deploy  \
    --dashboard-id cudos-v5 \
    --athena-database $database_name\
    --account-map-source dummy \
    --cur-table-name $cur_table \
    --quicksight-user $quicksight_user \
    --share-with-account \
    --quicksight-datasource-id $quicksight_datasource_id

  [ "$status" -eq 0 ]
}

@test "Views created" {
  run aws athena get-table-metadata \
    --catalog-name 'AwsDataCatalog'\
    --database-name $database_name \
    --table-name 'summary_view' \
 
 # FIXME: add
 #  compute_savings_plan_eligible_spend
 #  summary_view
 #  s3_view
 #  customer_all
 #  ec2_running_cost

  [ "$status" -eq 0 ]
}

@test "Dataset created" {
  run aws quicksight describe-data-set \
    --aws-account-id $account_id \
    --data-set-id d01a936f-2b8f-49dd-8f95-d9c7130c5e46

  [ "$status" -eq 0 ]
}

@test "Dashboard created" {
  run aws quicksight describe-dashboard \
    --aws-account-id $account_id \
    --dashboard-id cudos-v5

  [ "$status" -eq 0 ]
}

@test "Update works" {
  run cid-cmd -vv --yes update --force --recursive  \
    --dashboard-id cudos-v5 \
    --cur-table-name $cur_table \
    --quicksight-user $quicksight_user   \

  [ "$status" -eq 0 ]
}


@test "Delete runs" {
  run cid-cmd -vv --yes delete \
    --dashboard-id cudos-v5

  [ "$status" -eq 0 ]
}

@test "Dashboard is deleted" {
  run aws quicksight describe-dashboard \
    --aws-account-id $account_id \
    --dashboard-id cudos-v5

  [ "$status" -ne 0 ]
}

@test "Dataset is deleted" {
  run aws quicksight describe-data-set \
    --aws-account-id $account_id \
    --data-set-id d01a936f-2b8f-49dd-8f95-d9c7130c5e46

  [ "$status" -ne 0 ]
}

@test "View is deleted" {
  run aws athena get-table-metadata \
    --catalog-name 'AwsDataCatalog'\
    --database-name $database_name \
    --table-name 'summary_view'

  [ "$status" -ne 0 ]
}