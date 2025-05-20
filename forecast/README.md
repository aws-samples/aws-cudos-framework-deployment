# AWS CUDOS Cost Explorer Forecast Integration

This directory contains scripts and resources for integrating AWS Cost Explorer forecasting capabilities with the AWS CUDOS Framework.

## Overview

The Cost Explorer Forecast integration allows you to:

1. Collect AWS Cost Explorer forecast data
2. Store and transform this data for analysis
3. Visualize forecasts in QuickSight dashboards
4. Monitor spending trends and anticipate future costs

## Directory Structure

- `/scripts` - Contains shell scripts for data collection
  - `get_cost_forecast.sh` - Standalone script for collecting forecast data
- `/data-models` - Contains schemas and data transformation models
- `/quicksight` - Contains QuickSight visualization templates

## Usage

### Option 1: Using the cid-cmd Tool (Recommended)

```bash
# Generate forecast data
cid-cmd forecast

# Deploy the forecast dashboard
cid-cmd deploy --dashboard-id cost-forecast-dashboard
```

### Option 2: Using the Standalone Script

```bash
# Run the script directly
./scripts/get_cost_forecast.sh

# Optionally configure environment variables
AWS_DEFAULT_REGION=us-west-2 FORECAST_MONTHS=6 ./scripts/get_cost_forecast.sh
```

## Environment Variables

The scripts support the following environment variables:

- `AWS_DEFAULT_REGION` - AWS region to use (default: `us-east-1`)
- `FORECAST_BUCKET` - S3 bucket for storing data (default: `cid-data-{account-id}`)
- `FORECAST_PREFIX` - S3 prefix for forecast data (default: `cost-explorer-forecast`)
- `METRIC` - Cost metric to forecast (default: `UNBLENDED_COST`)
- `CONFIDENCE_LEVEL` - Prediction interval confidence level (default: `80`)
- `GRANULARITY` - Forecast granularity (default: `MONTHLY`)
- `FORECAST_MONTHS` - Number of months to forecast (default: `12`)
- `SERVICE_GROUPING` - Whether to group by service (default: `true`)

## Required Permissions

The following IAM permissions are required:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ce:GetCostForecast",
        "ce:GetDimensionValues"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::cid-data-*/*"
    }
  ]
}
```

## Further Information

For more detailed information, please refer to:

- [Cost Forecast Dashboard Documentation](../docs/cost_forecast.md)
- [AWS Cost Explorer Documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html)
