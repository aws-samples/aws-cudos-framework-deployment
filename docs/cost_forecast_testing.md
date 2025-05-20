# Testing the Cost Forecast Automation

This guide provides step-by-step instructions for testing the Cost Explorer forecast automation solution after deployment.

## Prerequisites

- AWS CLI configured with appropriate permissions
- Access to the AWS Management Console
- CloudFormation stack deployed successfully

## Step 1: Verify CloudFormation Resources

First, verify that all resources were created correctly by the CloudFormation stack:

```bash
# Check the stack status
aws cloudformation describe-stacks --stack-name cost-forecast-automation --query "Stacks[0].StackStatus"

# List the resources created by the stack
aws cloudformation list-stack-resources --stack-name cost-forecast-automation
```

Expected output should show `CREATE_COMPLETE` status and list the Lambda function, IAM role, S3 bucket (if created), and EventBridge rule.

## Step 2: Manually Trigger the Lambda Function

Instead of waiting for the scheduled execution, manually trigger the Lambda function to verify it works:

```bash
# Get the Lambda function name from the CloudFormation outputs
LAMBDA_FUNCTION=$(aws cloudformation describe-stacks --stack-name cost-forecast-automation --query "Stacks[0].Outputs[?OutputKey=='LambdaFunction'].OutputValue" --output text)

# Invoke the Lambda function
aws lambda invoke --function-name $LAMBDA_FUNCTION --payload '{}' response.json

# Check the response
cat response.json
```

You should see a success status code (200) in the response.

## Step 3: Verify S3 Data

Check that the forecast data was correctly written to S3:

```bash
# Get the S3 bucket name from CloudFormation outputs
S3_BUCKET=$(aws cloudformation describe-stacks --stack-name cost-forecast-automation --query "Stacks[0].Outputs[?OutputKey=='ForecastDataBucket'].OutputValue" --output text)

# List the forecast data files
aws s3 ls s3://$S3_BUCKET/cost-explorer-forecast/overall/ --recursive
aws s3 ls s3://$S3_BUCKET/cost-explorer-forecast/by-service/ --recursive
aws s3 ls s3://$S3_BUCKET/cost-explorer-forecast/partitioned/ --recursive

# Download the latest pointer file to check its content
aws s3 cp s3://$S3_BUCKET/cost-explorer-forecast/latest.json .
cat latest.json
```

You should see JSON files in the `overall` and possibly the `by-service` directories, as well as partitioned data in the `partitioned` directory. The `latest.json` file should contain a timestamp and path to the latest forecast data.

## Step 4: Check the Athena Table

Verify that the Athena table was created and contains the forecast data:

```bash
# Run an Athena query to check the table schema
aws athena start-query-execution \
  --query-string "DESCRIBE cost_forecast_data" \
  --query-execution-context Database=cid_cur \
  --result-configuration OutputLocation=s3://$S3_BUCKET/athena-results/

# Get the query execution ID and wait for completion
QUERY_ID=$(aws athena get-query-execution --query-execution-id <EXECUTION_ID> --query "QueryExecution.Status.State" --output text)

# Once completed, run a query to check the data
aws athena start-query-execution \
  --query-string "SELECT * FROM cost_forecast_data LIMIT 10" \
  --query-execution-context Database=cid_cur \
  --result-configuration OutputLocation=s3://$S3_BUCKET/athena-results/
```

Alternatively, you can use the AWS Management Console:

1. Open the Athena console
2. Select the `cid_cur` database
3. Run the query `SELECT * FROM cost_forecast_data LIMIT 10`
4. Verify that the results contain forecast data with dimensions, values, and forecast amounts

## Step 5: Verify CloudWatch Logs

Check the Lambda function logs for any errors or issues:

```bash
# Get the CloudWatch log group name for the Lambda
LOG_GROUP_NAME="/aws/lambda/$LAMBDA_FUNCTION"

# Get the latest log stream
LOG_STREAM=$(aws logs describe-log-streams --log-group-name $LOG_GROUP_NAME --order-by LastEventTime --descending --limit 1 --query "logStreams[0].logStreamName" --output text)

# Get the logs
aws logs get-log-events --log-group-name $LOG_GROUP_NAME --log-stream-name $LOG_STREAM
```

Look for successful completion messages and absence of error messages.

## Step 6: Test Dashboard Integration

To test the integration with the Cost Forecast Dashboard:

1. Deploy the Cost Forecast Dashboard if not already deployed:

```bash
cid-cmd deploy --dashboard-id cost-forecast-dashboard
```

2. Open the dashboard in QuickSight:

```bash
cid-cmd open --dashboard-id cost-forecast-dashboard
```

3. Verify that the dashboard displays the forecast data correctly:
   - Check that the forecast trend chart shows data
   - Verify that confidence intervals are displayed
   - Check that service breakdowns are available (if enabled)

## Step 7: Verify Scheduled Execution

To verify that the scheduled execution works:

1. Check the EventBridge rule:

```bash
aws events describe-rule --name CidCostForecastSchedule-$(aws configure get region)
```

2. Wait for the next scheduled execution or modify the schedule to run soon:

```bash
# Update the schedule to run 2 minutes from now
CURRENT_TIME=$(date -u +%H:%M)
MINUTE=$(date -u +%M)
HOUR=$(date -u +%H)
NEW_MINUTE=$(( (MINUTE + 2) % 60 ))
NEW_HOUR=$(( HOUR + (MINUTE + 2) / 60 ))

aws events put-rule --name CidCostForecastSchedule-$(aws configure get region) --schedule-expression "cron($NEW_MINUTE $NEW_HOUR * * ? *)"
```

3. After the scheduled time, check the CloudWatch logs and S3 bucket for new data.

## Troubleshooting

If tests fail, check these common issues:

1. **Lambda Execution Issues**:
   - Check CloudWatch logs for specific error messages
   - Verify IAM permissions for Cost Explorer, S3, and Glue
   - Increase Lambda timeout if execution is timing out

2. **Missing S3 Data**:
   - Verify S3 bucket permissions
   - Check that the Lambda function completed successfully
   - Ensure Cost Explorer API is available in your region

3. **Athena Table Issues**:
   - Verify the database exists and is accessible
   - Check that the table was created properly
   - Ensure the S3 location for the table is correct

4. **Dashboard Integration Issues**:
   - Verify the dashboard is using the correct dataset
   - Check that the forecast data is in the expected format
   - Ensure QuickSight permissions are set correctly

## Additional Validation

For a more thorough validation:

1. **Compare with manual data**:
   - Manually export Cost Explorer forecast data from the AWS Console
   - Compare the values with those collected by the automation

2. **Check multiple forecast periods**:
   - Modify the Lambda environment variables to collect different time periods
   - Verify data consistency across different time ranges

3. **Test different dimensions**:
   - Modify the function to collect forecasts for different dimensions (e.g., LINKED_ACCOUNT)
   - Verify the data is properly stored and queryable
