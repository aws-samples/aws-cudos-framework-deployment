export CID_VERSION=$(python3 -c "from cid import _version;print(_version.__version__)")

mkdir -p ./python
pip3 install . -t ./python
zip -qr cid-$CID_VERSION.zip ./python
ls cid-$CID_VERSION.zip
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

echo 'cleanup'
rm -vf ./cid-$CID_VERSION.zip
