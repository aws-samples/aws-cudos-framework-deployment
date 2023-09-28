#!/bin/bash
# This script can be used for release or testing of lambda layers upload.
export CID_VERSION=$(python3 -c "from cid import _version;print(_version.__version__)")
rm -rf build

echo 'Building a layer'
mkdir -p ./python
python3 -m pip install . -t ./python
zip -qr cid-$CID_VERSION.zip ./python
ls -l cid-$CID_VERSION.zip
rm -rf ./python

export AWS_REGION=us-east-1
export STACK_SET_NAME=LayerBuckets

aws cloudformation list-stack-instances \
  --stack-set-name $STACK_SET_NAME \
  --query 'Summaries[].[StackId,Region]' \
  --output text |
  while read stack_id region; do
    echo "uploading cid-$CID_VERSION.zip to $region"
    bucket=$(aws cloudformation list-stack-resources --stack-name $stack_id \
      --query 'StackResourceSummaries[?LogicalResourceId == `LayerBucket`].PhysicalResourceId' \
      --region $region --output text)
    output=$(aws s3api put-object \
      --bucket "$bucket" \
      --key cid-resource-lambda-layer/cid-$CID_VERSION.zip \
      --body ./cid-$CID_VERSION.zip)
    if [ $? -ne 0 ]; then
      echo "Error: $output"
    else
      echo "Uploaded successfuly"
    fi
  done

echo 'Cleanup'
rm -vf ./cid-$CID_VERSION.zip


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
