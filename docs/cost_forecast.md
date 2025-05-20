# AWS Cost Forecast Dashboard

The AWS Cost Forecast Dashboard provides a comprehensive view of your future AWS spending based on AWS Cost Explorer forecasts. This dashboard helps you predict and plan for future costs across different dimensions such as services, accounts, and regions.

## Features

- Visualize cost forecasts with confidence intervals
- Analyze forecasted costs by service, account, region, and other dimensions
- Compare forecasts across different metrics (Unblended Cost, Amortized Cost, etc.)
- View daily or monthly forecast granularity
- Identify potential cost spikes or anomalies in future spending

## Prerequisites

Before deploying the Cost Forecast Dashboard, ensure you have:

1. Completed the [general prerequisites](https://catalog.workshops.aws/awscid/en-US/dashboards/foundational/cudos-cid-kpi/deploy) (Steps 1 and 2)
2. AWS Cost Explorer enabled in your account
3. QuickSight Enterprise Edition activated

## Deployment Options

### Option 1: Main CloudFormation Deployment

The Cost Forecast Dashboard can be deployed along with other dashboards using the main CloudFormation template by setting the `DeployCostForecastDashboard` parameter to `yes`.

```bash
aws cloudformation deploy \
  --template-file cfn-templates/cid-cfn.yml \
  --stack-name cudos-framework \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides DeployCostForecastDashboard=yes
```

### Option 2: Using cid-cmd tool

Deploy the dashboard directly using the cid-cmd tool:

```bash
cid-cmd deploy --dashboard-id cost-forecast-dashboard
```

## Data Collection

This dashboard requires Cost Explorer forecast data to be collected separately. For automated data collection, please refer to the [Cloud Intelligence Dashboards Data Collection](https://github.com/aws-solutions-library-samples/cloud-intelligence-dashboards-data-collection/) repository.

### Manual Data Collection

You can also generate forecast data manually using the built-in forecast command:

```bash
cid-cmd forecast
```

Follow the interactive prompts to:
- Select the forecast time period
- Choose metrics and dimensions
- Set granularity (daily or monthly)
- Upload results to S3

## Dashboard Sections

### Cost Forecast Overview
- Trend chart showing forecasted costs over time with confidence intervals
- Distribution of forecasted costs by selected dimension
- Detailed forecast data table with confidence bounds

### Forecast Analysis
- Top services by forecasted cost
- Total forecasted cost KPI
- Forecast variance analysis

## Security and Permissions

The forecast command and dashboard require the following AWS IAM permissions:

- `ce:GetCostForecast` - To retrieve cost forecast data
- `ce:GetDimensionValues` - To retrieve dimension values for filtering
- `s3:PutObject` - To store forecast data in S3
- `athena:CreateTable` - To create the forecast data table
- QuickSight permissions for dataset and dashboard access

## Customization

You can customize the dashboard by:

1. Modifying the forecast parameters when generating data
2. Editing the QuickSight dashboard after deployment
3. Creating additional visualizations based on the forecast dataset

## Troubleshooting

If you encounter issues:

- Ensure AWS Cost Explorer is enabled in your account
- Verify you have sufficient permissions to access Cost Explorer APIs
- Check S3 bucket permissions if using S3 for data storage
- Run the forecast command with verbose logging: `cid-cmd forecast -vv`

## Additional Resources

- [AWS Cost Explorer Documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html)
- [AWS Cost Explorer API Reference](https://docs.aws.amazon.com/aws-cost-management/latest/APIReference/API_GetCostForecast.html)
- [QuickSight Documentation](https://docs.aws.amazon.com/quicksight/latest/user/welcome.html)
