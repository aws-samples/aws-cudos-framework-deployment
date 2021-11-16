export AWS_DEFAULT_REGION="us-east-1"
export AWS_DEFAULT_OUTPUT="text"
export AWS_PAGER=

awsAccountId=$(aws sts get-caller-identity --query 'Account')
dashboardId=${dashboardId:-lazymbr}

aws quicksight list-dashboard-versions \
    --aws-account-id ${awsAccountId} --dashboard-id ${dashboardId}
    --query 'sort_by(DashboardVersionSummaryList, &VersionNumber)[*].{version:VersionNumber}'
