#!/bin/bash
set -o pipefail
shopt -s extglob

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source "${DIR}/lib/common.sh"

export sourceTemplateId="${TRENDS_SOURCE_TEMPLATE_ID:-cudos-trends-dashboard-template}"
export dashboardId="${TRENDS_DASHBOARD_ID:-trends-dashboard}"

arguments=( "config" "prepare" "deploy-datasets" "deploy-dashboard" "map" "refresh-data-sets" "update-dashboard" "status" "delete" "cleanup" )

if [[ ! " ${arguments[*]} " == *" ${1} "* ]] || [ -z "$1" ]; then
  echo "Usage: ${myName} config | prepare | deploy-datasets | deploy-dashboard | map | refresh-data-sets | update-dashboard | status | delete | cleanup
    config: generates deployment config file
    prepare: creates Athena views based on the Usage
    deploy-datasets: creates QuickSight datasets
    deploy-dashboard: deploys the Trends dashboard
    map: generates aws_accounts Athena view containing account names
    refresh-data-sets: triggers SPICE refresh for Trends QuickSight datasets
    update-dashboard: updates the Trends dashboard to the latest release
    status: to debug failed deployments and get the status of the Trends dashboard
    delete: deletes the Trends dashboard from QuickSight
    cleanup: deletes the Trends datasets from QuickSight"
  exit 1
fi

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

case "$1" in

    config)

    config
    echo -e "\n####### Config created, now run ${myName} prepare\n"
    ;;

    deploy-datasets)
    # Get User ARN
    get_user_arn
    # Get CUR name
    athena_database_name
    get_cur_name
    PrepareDataSets
    CreateDatasets
    echo -e "\n####### QuickSight datasets created, now run ${myName} deploy-dashboard\n"
    ;;

    deploy-dashboard)

    get_user_arn
    check_existing_config

    # Generate create-dashboard json document
    { echo "cat <<EOF"
      cat dashboards/trends-create-dashboard.json
      echo "EOF"
    } | sh > $deployFileName
    echo "
    ####### Generated trends-create-dashboard.json
    "

    # Generate update-dashboard json document
    { echo "cat <<EOF"
      cat dashboards/trends-update-dashboard.json
      echo "EOF"
    } | sh > $updateFileName
    echo "
    ####### Generated trends-update-dashboard.json
    "

    echo "
    ####### Deploying Trends Dashboard
    "

    aws quicksight create-dashboard --region ${AWS_DEFAULT_REGION} --cli-input-json "file://${deployFileName}" --output table

    if [ $? -ne 0 ]
    then
       echo \"Something went wrong\"
       exit
    else

    sleep 20

    dashboard_state=$(aws quicksight describe-dashboard --region ${AWS_DEFAULT_REGION} --dashboard-id $dashboardId --aws-account-id $account --query 'Dashboard.Version.Status')

    if [ $dashboard_state != "CREATION_SUCCESSFUL" ]
    then
    echo "
    Something went wrong...
    To see the error run: ${myName} status
    To cleanup the failed deployment run: ${myName} delete
    To redeploy the failed deployment run: ${myName} deploy
    "
         exit 1
    fi

    echo "
    #######
    ####### Congratulations!
    ####### Trends Dashboard available here: https://${region}.quicksight.aws.amazon.com/sn/dashboards/$dashboardId
    ####### "

    fi
    ;;


    refresh-data-sets)

    aws quicksight create-ingestion --region ${AWS_DEFAULT_REGION} --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${account} --data-set-id 60e746ae-5781-4352-9752-dc9c633e21e4
    aws quicksight create-ingestion --region ${AWS_DEFAULT_REGION} --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${account} --data-set-id 0f11c81d-536a-405f-8de0-d0dc247627ad
    aws quicksight create-ingestion --region ${AWS_DEFAULT_REGION} --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${account} --data-set-id 69029320-c52c-4d21-86ad-3927bb2069f3

    ;;

    update-dashboard)
        # Check if the configuration exists
        check_existing_config
        [[ -f "${updateFileName}" ]] || (
            echo "ERROR: configuration file '${updateFileName}' not found, please run '${myName} deploy-dashboard'"
            exit 1
        )

    echo "Checking for updates..."

    echo -n "Getting latest available source template version..."
    latest_template_version=$(aws quicksight describe-template --query 'Template.Version.VersionNumber' \
        --aws-account-id ${sourceAccountId} --template-id ${sourceTemplateId} --region us-east-1)
    if [ $? -ne 0 ]
    then
       echo "unable to retreive latest template version number, please check you have requested accesss."
       exit
    fi
    echo "latest available template version is ${latest_template_version}"

    echo -n "Getting currently deployed source version..."
    current_dashboard_source_version=$(aws quicksight describe-dashboard --dashboard-id $dashboardId --query 'Dashboard.Version.SourceEntityArn' \
        --aws-account-id $account | cut -f 6 -d \: | cut -f 4 -d \/)
    if [ $? -ne 0 ]
    then
       echo "unable to retreive version number, please check you have dashboard deployed."
       exit
    fi
    echo "latest available template version is ${current_dashboard_source_version}"
    if [ ${current_dashboard_source_version} -eq ${latest_template_version} ]; then
        echo "You have the latest version deployed, no update required, exiting"
        exit
    elif [ ${current_dashboard_source_version} -gt ${latest_template_version} ]; then
        echo "Error: Your deployed version is newer than the latest template, please check your installation, exiting"
        exit
    fi

    echo "Update available ( ${current_dashboard_source_version} -> ${latest_template_version} ), proceeding"

    echo "
    ####### Pulling latest changes...
    "

    updated_dashboard_versionArn=$(aws quicksight update-dashboard --region ${AWS_DEFAULT_REGION} --cli-input-json "file://${updateFileName}" --query 'VersionArn')

    if [ $? -ne 0 ]
    then
       echo "Dashboard not available. Deploy the dashboard first."
       exit
    fi

    echo "
    ####### Applying latest changes to the deployed Dashboard...
    "

    updated_dashboard_versionStatus=$(aws quicksight list-dashboard-versions --aws-account-id $account --dashboard-id $dashboardId --query "DashboardVersionSummaryList[?Arn==\`${updated_dashboard_versionArn}\`].Status")

    if [ "$updated_dashboard_versionStatus" != "CREATION_SUCCESSFUL" ]; then
        echo "Error: something went wrong, exiting"
        exit
    fi
    updated_dashboard_versionNumber=$(aws quicksight list-dashboard-versions --region ${AWS_DEFAULT_REGION} --aws-account-id $account --dashboard-id $dashboardId --query "DashboardVersionSummaryList[?Arn==\`${updated_dashboard_versionArn}\`].VersionNumber")

    aws quicksight update-dashboard-published-version --aws-account-id $account --region ${AWS_DEFAULT_REGION} --dashboard-id $dashboardId --version-number $updated_dashboard_versionNumber --output table

    if [ $? -ne 0 ]
    then
       echo "Something went wrong"
       exit
    fi

    echo "

    #######
    ####### Congratulations!
    ####### Trends Dashboard updated to the latest version here: https://${region}.quicksight.aws.amazon.com/sn/dashboards/$dashboardId
    #######
    "
    ;;

    # Creates required Athena views
    prepare)

    # Get CUR name

    athena_database_name
    get_cur_name
    generate_queries
    generate_views

    echo -en "\n####### Checking if customer has RIs and/or SPs... "

    # Check if customer has RIs
    query_execution_id=$(execute_ahq_from_file "work/${account}/queries/ri_present.sql")
    ahq_ri_query_result=$(aws athena get-query-results --region ${AWS_DEFAULT_REGION} \
        --query-execution-id ${query_execution_id} --query 'length(ResultSet.Rows[])')

    # Check if customer has SPs
    query_execution_id=$(execute_ahq_from_file "work/${account}/queries/sp_present.sql")
    ahq_sp_query_result=$(aws athena get-query-results --region ${AWS_DEFAULT_REGION} \
        --query-execution-id ${query_execution_id} --query 'length(ResultSet.Rows[])')

    if [ "${ahq_ri_query_result}" -gt 1 ] && [ "${ahq_sp_query_result}" -gt 1 ]; then
        echo "both RIs and SPs"
        view_regex="*_sp_ri.sql"
    elif [ "${ahq_ri_query_result}" -gt 1 ] && [ "${ahq_sp_query_result}" -le 1 ]; then
        echo "RIs only"
        view_regex="!(*_sp)_ri.sql"
    elif [ "${ahq_ri_query_result}" -le 1 ] && [ "${ahq_sp_query_result}" -gt 1 ]; then
        echo "SPs only"
        view_regex="*_sp.sql"
    else
        echo "neither RIs nor SPs"
        view_regex="!(*_sp|*_ri).sql"
    fi
    echo -e "\n####### Creating Athena views..."
    for view in work/${account}/queries/account_mapping_dummy.sql work/${account}/views/${view_regex}; do
        echo $view
        ahq_query_execution_id=$(execute_ahq_from_file "${view}")
        echo -n "####### Executed query id: ${ahq_query_execution_id}, "
        ahq_query_status=$(ahq_query_status "${ahq_query_execution_id}")
        echo "status: ${ahq_query_status}"
    done
    echo -e "\n####### Athena views created, now run ${myName} deploy-datasets\n"

    ;;

    status)

    aws quicksight describe-dashboard --region ${AWS_DEFAULT_REGION} --dashboard-id $dashboardId --aws-account-id $account --output table

    ;;

    delete)

    aws quicksight delete-dashboard --region ${AWS_DEFAULT_REGION} --dashboard-id $dashboardId --aws-account-id $account --output table

    ;;

    cleanup)

    aws quicksight delete-data-source --aws-account-id $account --region ${AWS_DEFAULT_REGION} --data-source-id bd4dd2a3-7c40-4071-9bbb-6b5d2883537b
    aws quicksight delete-data-set --aws-account-id $account --region ${AWS_DEFAULT_REGION} --data-set-id 60e746ae-5781-4352-9752-dc9c633e21e4
    aws quicksight delete-data-set --aws-account-id $account --region ${AWS_DEFAULT_REGION} --data-set-id 0f11c81d-536a-405f-8de0-d0dc247627ad
    aws quicksight delete-data-set --aws-account-id $account --region ${AWS_DEFAULT_REGION} --data-set-id 69029320-c52c-4d21-86ad-3927bb2069f3
    aws glue batch-delete-table --database-name ${athena_database_name} --tables-to-delete "aws_accounts" "aws_regions" "aws_service_category_map" "daily_anomaly_detection" "monthly_anomaly_detection" "monthly_bill_by_account" "payer_account_name_map"
    ;;

    map)

    athena_database_name

    [[ -d "work/$account" ]] || mkdir -p "work/$account"

    echo -e "create or replace view aws_accounts as \nwith \nt1 as ( \nselect * \nfrom \n  (\n values"> work/${account}/account_map_view.sql

    aws organizations list-accounts --query 'Accounts[*].[Id,Status,Name,Email]' \
    --output text | awk '{print ",ROW ("  "'\''" $1 "'\''" ", " "'\''" $2 "'\''" ", " "'\''" $3 "'\''" ", " "'\''" $4 "'\''" ")"}' >> work/${account}/account_map_view.sql

    echo ") ignored_tabe_name (account_id, account_status, account_name, account_email_id)
),
t2 as (
select distinct line_item_usage_account_id, bill_payer_account_id FROM ${athena_cur_table_name} GROUP BY line_item_usage_account_id, bill_payer_account_id
      )
SELECT t1.*, t2.bill_payer_account_id AS parent_account_id FROM t1 LEFT JOIN t2 ON t1.account_id=t2.line_item_usage_account_id
    " >> work/${account}/account_map_view.sql

    if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "msys"* ]]; then
      sed -i "s/\"/\'/g;s/REPLACE/\,ROW\ /g;8s/\,//" work/${account}/account_map_view.sql
    elif [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i.bu "s/\"/\'/g;s/REPLACE/\,ROW\ /g;8s/\,//" work/${account}/account_map_view.sql
    fi

        echo -en "\nExecuting account_map query: "
        ahq_query_execution_id=$(execute_ahq_from_file "work/${account}/account_map_view.sql")
        echo "id: ${ahq_query_execution_id}, status: $(ahq_query_status "${ahq_query_execution_id}")"

        ;;
esac
