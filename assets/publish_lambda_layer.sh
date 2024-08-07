#!/bin/bash
# This script can be used for release or testing of lambda layers upload.

# First build layer
layer=$(./assets/build_lambda_layer.sh)

# Then publish on s3
export AWS_REGION=us-east-1
export STACK_SET_NAME=LayerBuckets
aws cloudformation list-stack-instances \
  --stack-set-name $STACK_SET_NAME \
  --query 'Summaries[].[StackId,Region]' \
  --output text |
  while read stack_id region; do
    echo "uploading $layer to $region"
    bucket=$(aws cloudformation list-stack-resources --stack-name $stack_id \
      --query 'StackResourceSummaries[?LogicalResourceId == `LayerBucket`].PhysicalResourceId' \
      --region $region --output text)
    output=$(aws s3api put-object \
      --bucket "$bucket" \
      --key cid-resource-lambda-layer/$layer \
      --body ./$layer)
    if [ $? -ne 0 ]; then
      echo "Error: $output"
    else
      echo "Uploaded successfuly"
    fi
  done

echo 'Cleanup'
rm -vf ./$layer


# Publish cfn (only works for the release)
if aws s3 ls "s3://aws-managed-cost-intelligence-dashboards" >/dev/null 2>&1; then
  echo "Updating cid-cfn.yml"
  aws s3 sync ./cfn-templates/ s3://aws-managed-cost-intelligence-dashboards/cfn/

  echo "Syncing dashboards"
  aws s3 sync ./dashboards s3://aws-managed-cost-intelligence-dashboards/hub/
else
  echo "Not the main account. Skipping"
fi

echo 'Done'
