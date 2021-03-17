#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source "${DIR}/lib/common.sh"

export sourceTemplateId="${CUDOS_SOURCE_TEMPLATE_ID:-cudos_dashboard_v3}"
export dashboardId="${CUDOS_DASHBOARD_ID:-cudos}"

datasets=("summary_view" "ec2_running_cost" "compute_savings_plan_eligible_spend" "s3_view" "customer_all")

# Try updating self to the latest version
#selfUpdate

echo "Checking environment"

# Check if we have correct aws cli version
check_aws_cli

# Check we are working with valid credentials
get_aws_account

# Check for config
if [ -e work/${account}/config ]; then
  source "work/${account}/config"
  echo "
  Config file detected work/${account}/config:"
  echo "----"
  cat work/${account}/config
  echo "----"
fi

# Get CUR region
get_cur_region

case "$1" in
    config)
      config
    ;;

    prepare)

    # Get CUR name

        athena_database_name
        get_cur_name
        get_user_arn

        generate_queries
        generate_views
        PrepareDataSets

        # Generate create-dashboard json document
        { echo "cat <<EOF"
          cat dashboards/create-dashboard.json
          echo "EOF"
        } | sh > work/${account}/deploy-dashboard.json

        # Generate update-dashboard json document
        { echo "cat <<EOF"
          cat dashboards/update-dashboard.json
          echo "EOF"
        } | sh > work/${account}/update-dashboard.json

#        echo -e "\n####### Checking if customer has RIs and/or SPs... "

        # Check if customer has RIs
        query_execution_id=$(execute_ahq_from_file "work/${account}/queries/ri_present.sql")
        ahq_ri_query_result=$(aws athena get-query-results \
            --query-execution-id ${query_execution_id} --query 'length(ResultSet.Rows[])')

        # Check if customer has SPs
        query_execution_id=$(execute_ahq_from_file "work/${account}/queries/sp_present.sql")
        ahq_sp_query_result=$(aws athena get-query-results \
            --query-execution-id ${query_execution_id} --query 'length(ResultSet.Rows[])')

        if [ "${ahq_ri_query_result}" -gt 1 ] && [ "${ahq_sp_query_result}" -gt 1 ]; then
            echo "both RIs and SPs"
            view_regex="*_sp_ri.sql"
        elif [ "${ahq_ri_query_result}" -gt 1 ] && [ "${ahq_sp_query_result}" -le 1 ]; then
            echo "RIs only"
            view_regex="*[!_sp]_ri.sql"
        elif [ "${ahq_ri_query_result}" -le 1 ] && [ "${ahq_sp_query_result}" -gt 1 ]; then
            echo "SPs only"
            view_regex="*_sp.sql"
        else
            echo "neither RIs nor SPs"
            view_regex="*[!_ri][!_sp].sql"
        fi

        echo -e "\n####### Please create go to Athena at
        https://console.aws.amazon.com/athena/home?region=${region}#
        and create views from these files:
        "
        for view in work/${account}/views/${view_regex} work/${account}/queries/account_mapping_dummy.sql; do
            echo $view
        done
        echo -e "\n####### After Athena views are created, run ${myName} deploy-datasets\n"

        ;;


    deploy-datasets)

        echo -e "\n####### Please create QuickSight datasource and datasets by running the following:

aws quicksight create-data-source --region ${region} --aws-account-id ${awsAccountId} --cli-input-json file://work/${account}/datasets/athena_datasource.json
aws quicksight create-data-set --region ${region} --aws-account-id ${awsAccountId} --cli-input-json file://work/${account}/datasets/summary_view-input_new.json
aws quicksight create-data-set --region ${region} --aws-account-id ${awsAccountId} --cli-input-json file://work/${account}/datasets/s3_view-input_new.json
aws quicksight create-data-set --region ${region} --aws-account-id ${awsAccountId} --cli-input-json file://work/${account}/datasets/compute_savings_plan_eligible_spend_new.json
aws quicksight create-data-set --region ${region} --aws-account-id ${awsAccountId} --cli-input-json file://work/${account}/datasets/ec2_running_cost_new.json
aws quicksight create-data-set --region ${region} --aws-account-id ${awsAccountId} --cli-input-json file://work/${account}/datasets/cur_new.json
        "

        echo -e "\n####### After QuickSight datasets are created, run ${myName} deploy-dashboard\n"
        ;;

    deploy-dashboard)

echo "
####### To deploy CUDOS Dashboard please run the following:

aws quicksight create-dashboard --region ${region} --cli-input-json \"file://work/${awsAccountId}/deploy-dashboard.json\"

####### To get the status of CUDOS Dashboard please run the following:

aws quicksight describe-dashboard --region ${region} --dashboard-id ${dashboardId} --aws-account-id ${awsAccountId} --query 'Dashboard.Version.Status'
"

    ;;

    refresh-data-sets)
    echo "
    aws quicksight create-ingestion --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${awsAccountId} --region ${region} --data-set-id d01a936f-2b8f-49dd-8f95-d9c7130c5e46
    aws quicksight create-ingestion --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${awsAccountId} --region ${region} --data-set-id 826896be-4d0f-4f90-832f-3427f5444016
    aws quicksight create-ingestion --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${awsAccountId} --region ${region} --data-set-id 3fa0d804-9bf5-4a20-a61d-4bdbb6d543b1
    aws quicksight create-ingestion --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${awsAccountId} --region ${region} --data-set-id 9497cc49-c9b1-4dcd-8bcc-c16396898f29
    "
    ;;

    update-dashboard)

      echo "\nPull the latest changes by running the following:
aws quicksight update-dashboard --region ${region} --cli-input-json "file://${updateFileName}" --query 'VersionArn'
"

echo "\nApply the latest changes by running the following:
aws quicksight update-dashboard-published-version --region ${region} --aws-account-id $account --dashboard-id $dashboardId --version-number \<LOCAL_VERSION_NUMBER\>
"

    ;;


    delete)
echo "Prease run to delete the CUDOS Dashboard
aws quicksight delete-dashboard --dashboard-id $dashboardId --region ${region} --aws-account-id $account
"
    ;;

    cleanup)

#    aws quicksight delete-dashboard --dashboard-id $dashboardId --aws-account-id $account --output table
echo "Delete CUDOS datasets from QuikcSight by running the following:
    aws quicksight delete-data-source --region ${region} --aws-account-id $account --data-source-id 95aa6f18-abb4-436f-855f-182b199a961f
    aws quicksight delete-data-set --region ${region} --aws-account-id $account --data-set-id d01a936f-2b8f-49dd-8f95-d9c7130c5e46
    aws quicksight delete-data-set --region ${region} --aws-account-id $account --data-set-id 826896be-4d0f-4f90-832f-3427f5444016
    aws quicksight delete-data-set --region ${region} --aws-account-id $account --data-set-id 3fa0d804-9bf5-4a20-a61d-4bdbb6d543b1
    aws quicksight delete-data-set --region ${region} --aws-account-id $account --data-set-id 9497cc49-c9b1-4dcd-8bcc-c16396898f29
    aws quicksight delete-data-set --region ${region} --aws-account-id $account --data-set-id 595c66b7-08b6-46ad-87ed-b74fe34dd333
"
    ;;

    map)

    athena_database_name

    [[ -d "work/$account" ]] || mkdir -p "work/$account"

    echo "create or replace view account_map as select * from ( values "> work/${account}/account_map_view.sql

    aws organizations list-accounts --query 'Accounts[*].{account_id:Id,account_name:Name}' \
    --output text | awk '{ saved = $1; $1 = ""; print ",ROW ( \""saved"\",", "\""substr($0, 2)":",saved,"\")" }' >> work/${account}/account_map_view.sql

    echo ") ignored_table_name (account_id, account_name)" >> work/${account}/account_map_view.sql

    if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "msys"* ]]; then
      sed -i "s/\"/\'/g;s/REPLACE/\,ROW\ /g;2s/\,//" work/${account}/account_map_view.sql
    elif [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i.bu "s/\"/\'/g;s/REPLACE/\,ROW\ /g;2s/\,//" work/${account}/account_map_view.sql
    fi

        echo -en "\nPlease run the account_map query in Athena: work/${account}/account_map_view.sql
        "


        ;;
*)

echo "Usage: ${myName} config | prepare | map | deploy-datasets | deploy-dashboard | delete | cleanup | update-dashboard | refresh-data-sets
  config: generates deoployment config file
  prepare: creates Athena views based on the Usage
  map: generates account_map Athena view containing account names
  deploy-datasets: creates QuickSight datasets
  deploy-dashboard: deploys the CUDOS dashboard
  update-dashboard: updates the CUDOS dashboard to the latest release
  refresh-data-sets: triggers SPICE refresh for CUDOS QuickSight datasets
  delete: deletes the CUDOS dashboard from QuickSight
  cleanup: deletes the CUDOS datasets from QuickSight"
;;

esac
