# Configure aws cli
export AWS_DEFAULT_OUTPUT="text"
export AWS_PAGER=

# Expose required variables
declare workpath="work/${account}"
export sourceAccountId="${CUDOS_SOURCE_ACCOUNT_ID:-223485597511}"
declare myName="${0}"

# Default values
required_cli_ver="2.1.17"
required_cli1x_ver="1.18.139"
aws_data_catalog_name="AwsDataCatalog"

# Tooling
git=$(which git)

function ver { printf "%03d%03d%03d%03d" $(echo "$1" | tr \. ' '); }
function major_ver { printf "%d" $(echo "$1" | cut -d\. -f1); }

function get_aws_cli_ver() { aws --version | cut -d\/ -f2 | cut -d' ' -f1; }

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
  get_cur_region
  get_qs_identity_region
  athena_database_name
  get_cur_name
  get_user_arn
  echo "export region=${aws_region}
export aws_identity_region=${aws_qs_identity_region}
export aws_qs_identity_region=${aws_qs_identity_region}
export athena_database_name=${aws_athena_database_name}
export athena_cur_table_name=${aws_athena_cur_table_name}
export user_arn=$qs_user_arn
export AWS_DEFAULT_REGION=${aws_region}" > work/${account}/config
  echo "
  config file stored in \"work/${account}/config\"
  "
}


function get_aws_account() {
    echo -n "Fetching AWS Account ID..."
    account=$(aws sts get-caller-identity --query "Account" --output text)
    export account=$account
    export awsAccountId=$account
    echo "ok"
}

function athena_database_name() {
  if [ "${athena_database_name}" = "" ]; then
    echo "Fetching Athena Database names..."
    databases=$(aws athena list-databases --region ${AWS_DEFAULT_REGION} --catalog-name AwsDataCatalog --query 'DatabaseList[*].Name' --output text)
    echo "Discovered Athena Database names.
Please select which one to use:
----"
    select aws_athena_database_name in $databases
    do
    echo "You have chosen $aws_athena_database_name"
    export athena_database_name=$aws_athena_database_name
    break
    done
  fi
}

function get_cur_name() {
    if [ "${athena_cur_table_name}" = "" ]; then
  [[ -d "work/$account/queries" ]] || mkdir -p "work/$account/queries"
#  for i in `ls queries-templates/athena_table_names.sql`; do
    { echo "cat <<EOF"
      cat queries-templates/athena_table_names.sql
      echo "EOF"
    } | sh > work/${account}/queries/athena_table_names.sql
#  done

    echo "Fetching Athena Table names..."
    ahq_query=$(<work/${account}/queries/athena_table_names.sql)
    query_execution_id=$(execute_ahq "${ahq_query}")
    echo "Discovered Athena Table names. . Please select which one to use:
----"
    ahq_query_result=$(aws athena get-query-results \
    --region ${AWS_DEFAULT_REGION} --query-execution-id ${query_execution_id} --query 'ResultSet.Rows[*].Data[*].VarCharValue' --output text)

    select aws_athena_cur_table_name in $ahq_query_result
    do
    echo "You have chosen $aws_athena_cur_table_name"
    export athena_cur_table_name=$aws_athena_cur_table_name
    break
    done
  fi
}

function get_cur_region() {
  if [ "${region}" = "" ]; then
    echo -n "Enter QuickSight region: "
    read aws_region
    export region=${aws_region}
    export AWS_DEFAULT_REGION=${aws_region}
  fi
}

function get_qs_identity_region() {
  if  [ "${aws_identity_region}" = "" ]; then
    echo -n "Enter QuickSight Identity region [default : ${region}]: "
    read aws_qs_identity_region
    if  [ "${aws_qs_identity_region}" = "" ]; then
      export aws_qs_identity_region=${region}
    fi
    export aws_identity_region=${aws_qs_identity_region}
  fi
}

function get_user_arn() {
  if [ "${user_arn}" = "" ]; then
    echo "Fetching QuickSight User ARNs..."
    # Fetching quicksight users, which may be from an alternate region from the dashboard deployment
    alias=$(aws quicksight list-users --aws-account-id ${account} --region ${aws_identity_region} --namespace default --query 'UserList[*].Arn' --output text)
    echo "Discovered QuickSight User ARNs.
Please select which one to use:
----"
    select qs_user_arn in $alias
    do
    echo "You have chosen $qs_user_arn"
    export user_arn=$qs_user_arn
    break
    done
  fi
}

function check_existing_config() {
    if [[ -f "deploy-dashboard-$account.json" ]] || [[ -f "$account-update-dashboard.json" ]]; then
        while true; do
            read -p "Detected legacy configuration, do you wish to migrate? " yn
            case $yn in
                [Yy]* )
                    echo -n "Migrating...";
                    [[ -d "work/$account" ]] || mkdir -p "work/$account"
                    mv "deploy-dashboard-$account.json" "work/$account/deploy-dashboard.json" || echo "deploy file not found.."
                    mv "update-dashboard-$account.json" "work/$account/update-dashboard.json" || echo "update file not found.."
                    echo "complete"
                    deployFileName="work/$account/deploy-dashboard.json"
                    deployCIDFileName="work/$account/deploy-cid-dashboard.json"
                    updateFileName="work/$account/update-dashboard.json"
                    break;;
                [Nn]* )
                    deployFileName="deploy-dashboard-$account.json"
                    updateFileName="update-dashboard-$account.json"
                    break;;
                * ) echo "Please answer yes or no.";;
            esac
        done
    else
        [[ -d "work/$account" ]] || mkdir -p "work/$account"
        deployFileName="work/$account/deploy-dashboard.json"
        deployCIDFileName="work/$account/deploy-cid-dashboard.json"
        updateFileName="work/$account/update-dashboard.json"
    fi
}

# Executes Athena queries, expects string, returns execution id
function execute_ahq() {
    local ahq_query="$1"
    query_execution_id=$(aws athena --region ${aws_region} start-query-execution \
        --query-execution-context Database=${athena_database_name},Catalog=${aws_data_catalog_name} \
        --work-group "primary" --query-string "${ahq_query}" --query 'QueryExecutionId')
    ahq_query_status=$(ahq_query_status "${query_execution_id}")
    while [ "${ahq_query_status}" = "RUNNING" ]; do
        sleep 1
        ahq_query_status=$(ahq_query_status "${query_execution_id}")
    done
    printf "${query_execution_id}"
}

function execute_ahq_from_file() {
    local ahq_query_file="$1"
    query_execution_id=$(aws athena --region ${AWS_DEFAULT_REGION} start-query-execution \
        --query-execution-context Database=${athena_database_name},Catalog=${aws_data_catalog_name} \
        --work-group "primary" --query-string "file://${ahq_query_file}" --query 'QueryExecutionId')
    ahq_query_status=$(ahq_query_status "${query_execution_id}")
    while [ "${ahq_query_status}" = "RUNNING" ]; do
        sleep 1
        ahq_query_status=$(ahq_query_status "${query_execution_id}")
    done
    printf "${query_execution_id}"
}

function ahq_query_status() {
    local query_execution_id="$1"
    ahq_query_status=$(aws athena --region ${AWS_DEFAULT_REGION} get-query-execution \
        --query-execution-id ${query_execution_id} --query 'QueryExecution.Status.State')
    printf "${ahq_query_status}"
}

function check_cur_enabled() {
    echo -n "Checking if CUR is enabled and available..."
    aws_data_catalog=$(aws athena --region ${AWS_DEFAULT_REGION} list-data-catalogs --query 'DataCatalogsSummary[?Type==`GLUE`].CatalogName')
    if [ "$aws_data_catalog" != "${aws_data_catalog_name}" ]; then
        echo "Error: please ensure CUR is enabled, allow it from 24 to 48 hours to propagate."
        exit 1
    fi
    aws_athena_database=$(aws athena --region ${AWS_DEFAULT_REGION} list-databases --catalog-name "${aws_data_catalog_name}" \
        --query "DatabaseList[?Name==\`${athena_database_name}\`].Name" )
    if [ "$aws_data_catalog" != "${aws_data_catalog_name}" ]; then
        echo "Error: please ensure CUR is enabled, allow it from 24 to 48 hours to propagate."
        exit 1
    fi
    # Check if customer has Resource Ids enabled
    ahq_query=$(<work/${account}/queries/resource_ids_present.sql)
    query_execution_id=$(execute_ahq "${ahq_query}")
    ahq_query_result=$(aws athena --region ${AWS_DEFAULT_REGION} get-query-results \
        --query-execution-id ${query_execution_id} --query 'length(ResultSet.Rows[])')
    if [ $ahq_query_result -le 1 ]; then
        echo "Error: Resource IDs not found in CUR"
        exit 1
    fi
    echo "ok"
}

function isInGitWorkDir() {
    [ -e ${git} ] && [ $(${git} rev-parse --is-inside-work-tree) ]
}

function selfUpdate() {
    set +e
    git fetch --dry-run
    isInGitWorkDir && ${git} pull
    if [ $? -ne 0 ]; then
        echo "Unable to update, do it manually if needed"
    fi
    set -e
}

function PrepareDataSets() {
  [[ -d "work/$account/datasets" ]] || mkdir -p "work/$account/datasets"
  for i in `ls dataset-templates`; do
    { echo "cat <<EOF"
      cat dataset-templates/$i
      echo "EOF"
    } | sh > work/${account}/datasets/$i
  done
}

function CreateDatasets() {
  aws quicksight create-data-source --aws-account-id ${awsAccountId} --region ${AWS_DEFAULT_REGION} --cli-input-json file://work/${account}/datasets/athena_datasource.json
  aws quicksight create-data-set --aws-account-id ${awsAccountId} --region ${AWS_DEFAULT_REGION} --cli-input-json file://work/${account}/datasets/summary_view-input_new.json
  aws quicksight create-data-set --aws-account-id ${awsAccountId} --region ${AWS_DEFAULT_REGION} --cli-input-json file://work/${account}/datasets/s3_view-input_new.json
  aws quicksight create-data-set --aws-account-id ${awsAccountId} --region ${AWS_DEFAULT_REGION} --cli-input-json file://work/${account}/datasets/compute_savings_plan_eligible_spend_new.json
  aws quicksight create-data-set --aws-account-id ${awsAccountId} --region ${AWS_DEFAULT_REGION} --cli-input-json file://work/${account}/datasets/ec2_running_cost_new.json
  aws quicksight create-data-set --aws-account-id ${awsAccountId} --region ${AWS_DEFAULT_REGION} --cli-input-json file://work/${account}/datasets/cur_new.json
}

function generate_queries() {
  [[ -d "work/$account/queries" ]] || mkdir -p "work/$account/queries"
  for i in `ls queries-templates | grep -v json`; do
    { echo "cat <<EOF"
      cat queries-templates/$i
      echo "EOF"
    } | sh > work/${account}/queries/$i
  done
}

function generate_views() {
  [[ -d "work/$account/views" ]] || mkdir -p "work/$account/views"
  for i in `ls view-templates | grep -v json`; do
    { echo "cat <<EOF"
      cat view-templates/$i
      echo "EOF"
    } | sh > work/${account}/views/$i
  done
}

function gitArchive() {
    isInGitWorkDir && ${git} archive -o work/latest.zip HEAD && echo -e "Created work/archive.zip"
}
