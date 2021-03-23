
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

source "${DIR}/lib/common.sh"
export sourceAccountId=223485597511
export sourceTemplateId="ta-organizational-view"
export dashboardId="ta-organizational-view"
export dataSourceId="ta-organizational-view"
export dataSetId="ta-organizational-view"
export athenaTable="ta_organizational_view_reports"
export AWS_DEFAULT_OUTPUT="text"

while [ $# -gt 0 ]; do
  case "$1" in
    --action=*)
      action="${1#*=}"
      ;;
    --account=*)
      account="${1#*=}"
      ;;
    --databaseName=*)
      databaseName="${1#*=}"
      ;;
    --s3FolderPath=*)
      s3FolderPath="${1#*=}"
      ;;
    --user_arn=*)
      user_arn="${1#*=}"
      ;;
    --region=*)
      region="${1#*=}"
      ;;
    --deploymentMode=*)
      deployment="${1#*=}"
      ;;
    *)
      printf "Invalid arguments\n"
      print_help
      ;;
  esac
  shift
done

check_aws_cli
get_aws_account
export cli_input_json_dir="work/$account/cli_configs"

if [ -z "${deploymentMode}" ]; then
  export deploymentMode="auto"
fi

case "$action" in
  prepare)
    config
    transform_templates
    echo "Please run ${myName} --action=deploy"
  ;;
  deploy)
    config
    deploy
  ;;
  delete)
    config
    delete
  ;;
  status)
    config
    status
  ;;
  update)
    config
    update
  ;;
  refresh-data)
    config
    refresh-data
  ;;
  *)
  printf "$action is not valid action\n"
  print_help
esac
