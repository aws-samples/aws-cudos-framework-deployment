export CID_VERSION=`python3 -c "from cid import _version;print(_version.__version__)"`

mkdir -p ./python
pip3 install . -t ./python
zip -r cid-$CID_VERSION.zip ./python
ls cid-$CID_VERSION.zip
rm -rf ./python


export STACK_SET_NAME=LayerBuckets

for region in $(
  aws cloudformation  list-stack-instances \
  --stack-set-name $STACK_SET_NAME \
  --query 'Summaries[].[Region]' \
  --output text \
); do
  echo "uploading cid-$CID_VERSION.zip to $region"
  output=$(aws s3api put-object \
    --bucket "aws-managed-cost-intelligence-dashboards-$region" \
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


