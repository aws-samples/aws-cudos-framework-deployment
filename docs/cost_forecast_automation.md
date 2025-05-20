# AWS Cost Explorer Forecast Automation

This document explains how to set up automated collection of AWS Cost Explorer forecast data for use with the CUDOS framework.

## Overview

The AWS Cost Explorer Forecast Automation solution sets up a scheduled Lambda function that periodically collects cost forecast data from the AWS Cost Explorer API and stores it in the proper format for the Cost Forecast Dashboard.

This solution:

1. Creates a Lambda function that collects forecast data from AWS Cost Explorer
2. Schedules the Lambda function to run on a regular basis using EventBridge
3. Stores the data in an S3 bucket in formats ready for visualization
4. Optionally creates an Athena table to query the forecast data

## Prerequisites

Before deploying this solution, ensure you have:

1. AWS Cost Explorer enabled in your account
2. Appropriate permissions to create CloudFormation stacks, Lambda functions, IAM roles, and S3 buckets
3. The CUDOS framework deployed in your account

## Deployment Instructions

### Option 1: Using the AWS Management Console

1. Open the AWS CloudFormation console
2. Choose "Create stack" and select "With new resources (standard)"
3. Upload the `cost-forecast-collection.yaml` template
4. Provide values for the parameters:
   - `ScheduleExpression`: When to run the forecast collection (default: daily at 1:00 AM UTC)
   - `ForecastMonths`: How many months to forecast (default: 12)
   - `ServiceGrouping`: Whether to group forecasts by service (default: true)
   - `Granularity`: DAILY or MONTHLY forecasts (default: MONTHLY)
   - `ConfidenceLevel`: Confidence level for predictions (default: 80%)
   - `CostMetric`: Which cost metric to forecast (default: UNBLENDED_COST)
   - `ForecastBucket`: Custom S3 bucket name (leave empty to create default)
   - `ForecastPrefix`: S3 prefix for forecast data (default: cost-explorer-forecast)
   - `CidDatabaseName`: Athena database name (default: cid_cur)
5. Complete the stack creation wizard and wait for the stack to deploy

### Option 2: Using the AWS CLI

```bash
aws cloudformation create-stack \
  --stack-name cost-forecast-automation \
  --template-body file://cfn-templates/cost-forecast-collection.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters \
    ParameterKey=ScheduleExpression,ParameterValue='cron(0 1 * * ? *)' \
    ParameterKey=ForecastMonths,ParameterValue=12 \
    ParameterKey=Granularity,ParameterValue=MONTHLY
```

## Integration with Cost Forecast Dashboard

After deploying the automation solution:

1. Ensure the Lambda function has run at least once to generate forecast data
2. Deploy the Cost Forecast Dashboard using:

```bash
cid-cmd deploy --dashboard-id cost-forecast-dashboard
```

The dashboard will automatically use the data collected by the automation solution.

## Customization

### Schedule Expressions

The solution uses EventBridge schedule expressions. Some common patterns:

- Daily at midnight UTC: `cron(0 0 * * ? *)`
- Weekly on Monday at 9:00 AM UTC: `cron(0 9 ? * MON *)`
- Monthly on the 1st at 6:00 AM UTC: `cron(0 6 1 * ? *)`

### Forecast Parameters

The solution allows customizing:

- **Forecast Period**: How many months into the future to forecast (1-12)
- **Granularity**: Daily or monthly data points
- **Confidence Level**: The confidence interval for forecasts (50-95%)
- **Grouping**: Whether to group forecasts by service

## Monitoring

You can monitor the forecast collection process through:

- CloudWatch Logs: Check the logs of the Lambda function
- S3: Verify new forecast data is being stored in the S3 bucket
- CloudWatch Metrics: View Lambda execution metrics

## Troubleshooting

Common issues:

1. **Lambda timeouts**: If forecasts take too long, increase the Lambda timeout
2. **Missing permissions**: Ensure the Lambda role has proper Cost Explorer permissions
3. **No data appearing**: Check CloudWatch Logs for errors in the Lambda function

## Data Structure

The automation solution stores forecast data in two formats:

1. **Raw forecast data**: JSON responses from the Cost Explorer API
2. **Partitioned data**: Processed data ready for Athena queries

Data is organized in S3 with the following structure:

```
s3://bucket-name/cost-explorer-forecast/
├── overall/                     # Overall forecasts (no grouping)
│   └── YYYY-MM-DD-HH-MM-SS.json # Timestamp-named files
├── by-service/                  # Service-grouped forecasts
│   └── YYYY-MM-DD-HH-MM-SS.json
├── partitioned/                 # Athena-friendly partitioned data
│   └── year=YYYY/
│       └── month=MM/
│           ├── overall.json
│           └── by-service.json
└── latest.json                  # Pointer to most recent forecast
```

## Security Considerations

The solution follows security best practices:

- Least privilege permissions for the Lambda function
- S3 bucket with encryption and access controls
- No public access to resources
- CloudWatch Logs for audit and monitoring

## Cost Impact

This solution incurs costs from:

- Lambda invocations (minimal for daily execution)
- S3 storage for forecast data (minimal)
- Cost Explorer API calls (check AWS pricing)

## Testing the Deployment

After deploying the solution, it's important to verify that everything is working correctly. A brief testing procedure:

1. **Verify the CloudFormation stack** was created successfully
2. **Manually trigger the Lambda function** to test the data collection
3. **Check the S3 bucket** for the generated forecast data
4. **Verify integration with dashboards** by deploying the forecast dashboard

For detailed step-by-step testing instructions, please refer to the [Cost Forecast Testing Guide](cost_forecast_testing.md).

## Uninstalling

To remove the solution:

1. Delete the CloudFormation stack
2. Optionally delete the S3 data (if not deleted by CloudFormation)
