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
aws s3 ls aws-managed-cost-intelligence-dashboards
if [ $? -eq 0 ]; then
  echo "Updating cid-cfn.yml"
  aws s3api put-object \
        --bucket "aws-managed-cost-intelligence-dashboards" \
        --key cfn/cid-cfn.yml \
        --body ./cfn-templates/cid-cfn.yml
else
  echo "Not a main account. Skipping update of cid-cfn.yml"
fi

echo 'Done'
