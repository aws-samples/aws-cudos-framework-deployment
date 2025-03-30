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

### Option 1: Using cid-cmd tool (Recommended)

1. Generate forecast data using the built-in forecast command:

```bash
cid-cmd forecast
```

2. Follow the interactive prompts to:
   - Select the forecast time period
   - Choose metrics and dimensions
   - Set granularity (daily or monthly)
   - Upload results to S3

3. Deploy the dashboard:

```bash
cid-cmd deploy --dashboard-id cost-forecast-dashboard
```

### Option 2: Using the standalone script

If you prefer to use the standalone script for more control over the forecast data collection:

1. Run the script from the scripts directory:

```bash
cd scripts
./cost_forecast.sh
```

2. Follow the interactive prompts to configure and generate the forecast data

3. After uploading to S3, deploy the dashboard:

```bash
cid-cmd deploy --dashboard-id cost-forecast-dashboard
```

## Dashboard Sections

### Cost Forecast Overview
- Trend chart showing forecasted costs over time with confidence intervals
- Distribution of forecasted costs by selected dimension
- Detailed forecast data table with confidence bounds

### Forecast Analysis
- Top services by forecasted cost
- Total forecasted cost KPI
- Forecast variance analysis

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
