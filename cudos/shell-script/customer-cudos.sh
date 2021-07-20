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
  cat dashboards/create-dashboard.json
  echo "EOF"
} | sh > $deployFileName
echo "
####### Generated deploy-dashboard.json
"

# Generate update-dashboard json document
{ echo "cat <<EOF"
  cat dashboards/update-dashboard.json
  echo "EOF"
} | sh > $updateFileName
echo "
####### Generated update-dashboard.json
"

echo "
####### Deploying CUDOS Dashboard
"

aws quicksight create-dashboard --region ${AWS_DEFAULT_REGION} --cli-input-json "file://${deployFileName}" --output table

if [ $? -ne 0 ]
then
   echo \"Something went wrong\"
   exit
else

  sleep 45

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
####### CUDOS Dashboard available here: https://${region}.quicksight.aws.amazon.com/sn/dashboards/$dashboardId
####### "

fi
    ;;

    deploy-cid-dashboard)
    get_user_arn

    check_existing_config


# Generate create-cid-dashboard json document
{ echo "cat <<EOF"
  cat dashboards/create-cid-dashboard.json
  echo "EOF"
} | sh > $deployCIDFileName
echo "
####### Generated deploy-cid-dashboard.json
"

echo "
####### Deploying CID Dashboard
"

aws quicksight create-dashboard --region ${AWS_DEFAULT_REGION} --cli-input-json "file://${deployCIDFileName}" --output table


    ;;

    refresh-data-sets)

    aws quicksight create-ingestion --region ${AWS_DEFAULT_REGION} --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${account} --data-set-id d01a936f-2b8f-49dd-8f95-d9c7130c5e46
    aws quicksight create-ingestion --region ${AWS_DEFAULT_REGION} --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${account} --data-set-id 826896be-4d0f-4f90-832f-3427f5444016
    aws quicksight create-ingestion --region ${AWS_DEFAULT_REGION} --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${account} --data-set-id 3fa0d804-9bf5-4a20-a61d-4bdbb6d543b1
    aws quicksight create-ingestion --region ${AWS_DEFAULT_REGION} --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${account} --data-set-id 9497cc49-c9b1-4dcd-8bcc-c16396898f29

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
if [[ "${current_dashboard_source_version}" -eq "${latest_template_version}" ]]; then
    echo "You have the latest version deployed, no update required, exiting"
    exit
elif [[ "${current_dashboard_source_version}" -gt "${latest_template_version}" ]]; then
    echo "Error: Your deployed version is newer than the latest template, please check your installation, exiting"
    exit
fi

echo "Update available ( ${current_dashboard_source_version} > ${latest_template_version} ), proceeding"

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
####### CUDOS Dashboard updated to the latest version here: https://${region}.quicksight.aws.amazon.com/sn/dashboards/$dashboardId
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
    view_regex="*[!_sp]_ri.sql"
elif [ "${ahq_ri_query_result}" -le 1 ] && [ "${ahq_sp_query_result}" -gt 1 ]; then
    echo "SPs only"
    view_regex="*_sp.sql"
else
    echo "neither RIs nor SPs"
    view_regex="*[!_ri][!_sp].sql"
fi

        echo -e "\n####### Creating Athena views..."
        for view in work/${account}/views/${view_regex} work/${account}/queries/account_mapping_dummy.sql; do
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

    cid-delete)

    aws quicksight delete-dashboard --region ${AWS_DEFAULT_REGION} --dashboard-id cost_intelligence_dashboard --aws-account-id $account --output table

    ;;

    cleanup)

#    aws quicksight delete-dashboard --dashboard-id $dashboardId --aws-account-id $account --output table
    aws quicksight delete-data-source --aws-account-id $account --region ${AWS_DEFAULT_REGION} --data-source-id 95aa6f18-abb4-436f-855f-182b199a961f
    aws quicksight delete-data-set --aws-account-id $account --region ${AWS_DEFAULT_REGION} --data-set-id d01a936f-2b8f-49dd-8f95-d9c7130c5e46
    aws quicksight delete-data-set --aws-account-id $account --region ${AWS_DEFAULT_REGION} --data-set-id 826896be-4d0f-4f90-832f-3427f5444016
    aws quicksight delete-data-set --aws-account-id $account --region ${AWS_DEFAULT_REGION} --data-set-id 3fa0d804-9bf5-4a20-a61d-4bdbb6d543b1
    aws quicksight delete-data-set --aws-account-id $account --region ${AWS_DEFAULT_REGION} --data-set-id 9497cc49-c9b1-4dcd-8bcc-c16396898f29
    aws quicksight delete-data-set --aws-account-id $account --region ${AWS_DEFAULT_REGION} --data-set-id 595c66b7-08b6-46ad-87ed-b74fe34dd333

    ;;

    map)

    athena_database_name

    [[ -d "work/$account" ]] || mkdir -p "work/$account"

    echo "create or replace view account_map as select * from ( values "> work/${account}/account_map_view.sql

    aws organizations list-accounts --query 'Accounts[*].{account_id:Id,account_name:Name}' \
    --output text | awk '{ saved = $1; $1 = ""; print ",ROW ( \""saved"\",", "\""substr($0, 2)":",saved,"\")" }' >> work/${account}/account_map_view.sql

    echo ") ignored_tabe_name (account_id, account_name)" >> work/${account}/account_map_view.sql

    if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "msys"* ]]; then
      sed -i "s/\"/\'/g;s/REPLACE/\,ROW\ /g;2s/\,//" work/${account}/account_map_view.sql
    elif [[ "$OSTYPE" == "darwin"* ]]; then
      sed -i.bu "s/\"/\'/g;s/REPLACE/\,ROW\ /g;2s/\,//" work/${account}/account_map_view.sql
    fi

        echo -en "\nExecuting account_map query: "
        ahq_query_execution_id=$(execute_ahq_from_file "work/${account}/account_map_view.sql")
        echo "id: ${ahq_query_execution_id}, status: $(ahq_query_status "${ahq_query_execution_id}")"

        ;;
*)

echo "Usage: ${myName} config | prepare | deploy-datasets | deploy-dashboard | delete | cleanup | update-dashboard | refresh-data-sets | status | map
  config: generates deoployment config file
  prepare: creates Athena views based on the Usage
  map: generates account_map Athena view containing account names
  deploy-datasets: creates QuickSight datasets
  deploy-dashboard: deploys the CUDOS dashboard
  deploy-cid-dashboard: deploys the CID dashboard
  update-dashboard: updates the CUDOS dashboard to the latest release
  refresh-data-sets: triggers SPICE refresh for CUDOS QuickSight datasets
  status: to debug failed deployments and get the status of the CUDOS dashboard
  delete: deletes the CUDOS dashboard from QuickSight
  cid-delete: deletes the CID dashboard from QuickSight
  cleanup: deletes the CUDOS datasets from QuickSight"
;;

esac
