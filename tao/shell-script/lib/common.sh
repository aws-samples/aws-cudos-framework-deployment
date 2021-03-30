declare myName="${0}"

required_cli_ver="2.1.16"
function get_aws_cli_ver() { aws --version | cut -d\/ -f2 | cut -d' ' -f1; }
function ver { printf "%03d%03d%03d%03d" $(echo "$1" | tr \. ' '); }
function major_ver { printf "%d" $(echo "$1" | cut -d\. -f1); }

function check_aws_cli() {
    # Check if a user has at least the minimal required aws cli installed
    awscli_ver=$(get_aws_cli_ver)
    echo -n "AWS CLI version...${awscli_ver}..."
    if [ $(major_ver ${awscli_ver}) -eq "2" ] && [ $(ver ${awscli_ver}) -lt $(ver "${required_cli_ver}") ]; then
        echo "Error: at least AWS CLI v2 version ${required_cli_ver} required, please upgrade"
        if [ `whoami` = "cloudshell-user" ]; then
          echo "CloudShell detected you can upgrade your CloudShell AWS CLI running the following commands:
          curl \"https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip\" -o ~/awscliv2.zip
          unzip ~/awscliv2.zip -d ~/
          sudo ~/aws/install --update"
        fi
        exit 1
    fi
    if [ $(major_ver ${awscli_ver}) -eq "1" ] && [ $(ver ${awscli_ver}) -lt $(ver "${required_cli1x_ver}") ]; then
        echo "Error: at least AWS CLI version ${required_cli1x_ver} required, please upgrade"
        exit 1
    fi
    echo "ok"
}

function config() {
  # Check for config
  if [ -e work/${account}/config ]; then
    source "work/${account}/config"
    echo "
    Config file detected work/${account}/config:"
    echo "----"
    cat work/${account}/config
    echo "----"
    return 0
  fi
  if [ -z "${s3FolderPath}" ]; then
    get_s3FolderPath
  fi
  if [ -z "${region}" ]; then
    get_region
  fi
  if [ -z "${user_arn}" ]; then
    get_user_arn
  fi
  if [ -z "${databaseName}" ]; then
    get_athena_database_name
  fi
  [[ -d "work/$account/" ]] || mkdir -p "work/$account/"
  echo "export region=${region}
export databaseName=${databaseName}
export s3FolderPath=${s3FolderPath}
export user_arn=$user_arn
export AWS_DEFAULT_REGION=${region}" > work/${account}/config
  echo "
  config file stored in \"work/${account}/config\"
  "
}

function transform_templates() {
  echo 'Transforming templates into configs...'
  [[ -d "${cli_input_json_dir}" ]] || mkdir -p "${cli_input_json_dir}"
 # export databaseName=${databaseName}
  for i in `ls templates`; do
    { echo "cat <<EOF"
      cat templates/$i
      echo "EOF"
    } | sh > ${cli_input_json_dir}/$i
  done
  echo 'Done!'
}
function get_user_arn() {
    echo "Fetching QuickSight User ARNs..."
    alias=$(aws quicksight list-users --aws-account-id ${account} --namespace default --region ${region} --query 'UserList[*].Arn' --output text)
    echo "Discovered QuickSight User ARNs. Please select which one to use:"
    select qs_user_arn in $alias
    do
    echo "You have chosen $qs_user_arn"
    export user_arn=$qs_user_arn
    break
    done
}
function get_athena_database_name() {
    echo "Fetching Athena Database names..."
    databases=$(aws athena list-databases --catalog-name AwsDataCatalog --query 'DatabaseList[*].Name' --output text)
    echo "Discovered Athena Database names. Please select which one to use:
----"
    databases+=('create-new-database')
    select selection in ${databases[@]}
    do
    if [[ "$selection" == "create-new-database" ]] ; then
      echo -n "Enter database name to create:"
      read databaseName
      if [[ "${deploymentMode}" == "auto" ]] ; then
        aws glue create-database --database-input "{\"Name\":\"$databaseName\"}"
        export databaseName=$databaseName
      else
        echo "Please run following command to create glue database and re-run the script:
        aws glue create-database --database-input \"{\\\"Name\\\":\\\"$databaseName\\\"}\"
        "
        exit
      fi
      break
    else
      echo "You have chosen $selection"
      export databaseName=$selection
    fi
    break
    done
}

function get_aws_account() {
    echo -n "Fetching AWS Account ID..."
    account=$(aws sts get-caller-identity --query "Account" --output text)
    echo "Working in $account account"
    export account=$account
}

function get_s3FolderPath() {
    echo -n "Enter S3 bucket name with TA organizational view reports:"
    read bucket_name
    export s3FolderPath="s3://${bucket_name}/reports/"
}

function get_region() {
    echo -n "Enter QuickSight region: "
    read aws_region
    export region=${aws_region}
    export AWS_DEFAULT_REGION=${aws_region}
}
function get_deployment_mode() {
  echo "Please select deployment mode:"
  select deployment in manual automated
  do
  echo "You have selected $deployment"
  export deploymentMode=$deployment
  break
  done
}

function print_help(){
  echo "Usage: ${myName}  --action={action}
  action: one of following actions:
        prepare - generates config files from templates
        deploy - deploys Athena table and QuickSight datasource, dataset and dashboard
        delete - deletes Athena table and QuickSight datasource, dataset and dashboard
        update - updates QuickSight dashboard to latest available version
        status - display status of dashboard creation
        refresh-data - refreshes dataset in QuickSight SPICE"
        
  exit 1
}


function deploy() {
  if [[ "$deploymentMode" == "auto" ]] ; then
    echo "aws glue create-table --cli-input-json file://${cli_input_json_dir}/athena-table.json"
    aws glue create-table --cli-input-json file://${cli_input_json_dir}/athena-table.json
    echo "aws quicksight create-data-source --aws-account-id ${account} --cli-input-json file://${cli_input_json_dir}/data-source-input.json"
    aws quicksight create-data-source --aws-account-id ${account} --cli-input-json file://${cli_input_json_dir}/data-source-input.json
    echo "aws quicksight create-data-set --aws-account-id ${account} --cli-input-json file://${cli_input_json_dir}/data-set-input.json"
    aws quicksight create-data-set --aws-account-id ${account} --cli-input-json file://${cli_input_json_dir}/data-set-input.json
    echo "aws quicksight create-dashboard --aws-account-id ${account} --cli-input-json file://${cli_input_json_dir}/dashboard-input.json"
    aws quicksight create-dashboard --aws-account-id ${account} --cli-input-json file://${cli_input_json_dir}/dashboard-input.json
    if [ $? -ne 0 ]
    then
       echo \"Something went wrong\"
       exit
    fi
    status
  else
       echo "Please run the following commands to deploy dashboard:
       aws glue create-table --cli-input-json file://${cli_input_json_dir}/athena-table.json
       aws quicksight create-data-source --aws-account-id ${account} --cli-input-json file://${cli_input_json_dir}/data-source-input.json
       aws quicksight create-data-set --aws-account-id ${account} --cli-input-json file://${cli_input_json_dir}/data-set-input.json
       aws quicksight create-dashboard --aws-account-id ${account} --cli-input-json file:/${cli_input_json_dir}/dashboard-input.json
         "
  fi
}

function delete() {
  if [[ "$deploymentMode" == "auto" ]] ; then
    echo "aws glue delete-table --database-name ${databaseName} --name ta_organizational_view_reports"
    aws glue delete-table --database-name ${databaseName} --name ta_organizational_view_reports
    echo "aws quicksight delete-data-source --aws-account-id ${account} --data-source-id ta-organizational-view"
    aws quicksight delete-data-source --aws-account-id ${account} --data-source-id ta-organizational-view
    echo "aws quicksight delete-data-set --aws-account-id ${account} --data-set-id ta-organizational-view"
    aws quicksight delete-data-set --aws-account-id ${account} --data-set-id ta-organizational-view
    echo "aws quicksight delete-dashboard --aws-account-id ${account} --dashboard-id ta-organizational-view"
    aws quicksight delete-dashboard --aws-account-id ${account} --dashboard-id ta-organizational-view
  else
    echo "Please run the following commands to delete dashboard:
    aws glue delete-table --database-name ${databaseName} --name ta_organizational_view_reports
    aws quicksight delete-data-source --aws-account-id ${account} --data-source-id ${dataSourceId}
    aws quicksight delete-data-set --aws-account-id ${account} --data-set-id ${dataSetId}
    aws quicksight delete-dashboard --aws-account-id ${account} --dashboard-id ${dashboardId}
      "
  fi
}

function status() {
    dashboard_state=$(aws quicksight describe-dashboard --dashboard-id $dashboardId --aws-account-id $account --query 'Dashboard.Version.Status')

    if [ $dashboard_state != "CREATION_SUCCESSFUL" ]
    then
    echo "
    Something went wrong...
    To see the error run: ${myName} --action=status
    To cleanup the failed deployment run: ${myName} --action=delete
    To redeploy the failed deployment run: ${myName} --action=deploy
    "
         exit 1
    fi

    echo "
    #######
    ####### TAO Dashboard available here: https://${region}.quicksight.aws.amazon.com/sn/dashboards/$dashboardId
    ####### "
    
}

function refresh-data() {
  aws quicksight create-ingestion --ingestion-id `date +%Y_%m_%H_%M` --aws-account-id ${account} --data-set-id ${dataSetId}
}
function update() {
  echo "Checking for updates..."
  echo -n "Getting latest available source template version..."
  latest_template_version=$(aws quicksight describe-template --query 'Template.Version.VersionNumber' \
      --aws-account-id ${sourceAccountId} --template-id ${sourceTemplateId})
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

  echo "Update available ( ${current_dashboard_source_version} > ${latest_template_version} ), proceeding"

  if [[ "$deploymentMode" != "auto" ]] ; then
    echo "Please run following commands to get updates:
      1. aws quicksight update-dashboard --aws-account-id ${account} --cli-input-json file://${cli_input_json_dir}/update-dashboard-input.json
      2. aws quicksight list-dashboard-versions --aws-account-id ${account}  --dashboard-id $dashboardId --query "DashboardVersionSummaryList[-1].VersionNumber" | xargs -I {} aws quicksight update-dashboard-published-version --aws-account-id ${account} --dashboard-id $dashboardId --version-number {}
    " 
    exit
  fi
  echo "
  ####### Pulling latest changes...
  "

  updated_dashboard_versionArn=$(aws quicksight update-dashboard --cli-input-json "file://${cli_input_json_dir}/update-dashboard-input.json" --query 'VersionArn')

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
  updated_dashboard_versionNumber=$(aws quicksight list-dashboard-versions --aws-account-id $account --dashboard-id $dashboardId --query "DashboardVersionSummaryList[?Arn==\`${updated_dashboard_versionArn}\`].VersionNumber")

  aws quicksight update-dashboard-published-version --aws-account-id $account --dashboard-id $dashboardId --version-number $updated_dashboard_versionNumber --output table

  if [ $? -ne 0 ]
  then
     echo "Something went wrong"
     exit
  fi

  echo "

  #######
  ####### Dashboard updated to the latest version here: https://${region}.quicksight.aws.amazon.com/sn/dashboards/$dashboardId
  #######
  "
}
