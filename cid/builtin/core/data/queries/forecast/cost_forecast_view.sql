-- Create a view for cost forecast data
CREATE OR REPLACE VIEW ${athena_database_name}.cost_forecast AS
SELECT 
    dimension,
    value,
    metric,
    CAST(startdate AS date) AS start_date,
    CAST(enddate AS date) AS end_date,
    CAST(meanvalue AS decimal(18,4)) AS mean_value,
    CAST(lowerbound AS decimal(18,4)) AS lower_bound,
    CAST(upperbound AS decimal(18,4)) AS upper_bound,
    CASE 
        WHEN metric = 'UNBLENDED_COST' THEN 'Unblended Cost'
        WHEN metric = 'BLENDED_COST' THEN 'Blended Cost'
        WHEN metric = 'AMORTIZED_COST' THEN 'Amortized Cost'
        WHEN metric = 'NET_UNBLENDED_COST' THEN 'Net Unblended Cost'
        WHEN metric = 'NET_AMORTIZED_COST' THEN 'Net Amortized Cost'
        WHEN metric = 'USAGE_QUANTITY' THEN 'Usage Quantity'
        WHEN metric = 'NORMALIZED_USAGE_AMOUNT' THEN 'Normalized Usage'
        ELSE metric
    END AS metric_name,
    CASE
        WHEN dimension = 'SERVICE' THEN 'AWS Service'
        WHEN dimension = 'LINKED_ACCOUNT' THEN 'Account ID'
        WHEN dimension = 'LINKED_ACCOUNT_NAME' THEN 'Account Name'
        WHEN dimension = 'REGION' THEN 'Region'
        WHEN dimension = 'USAGE_TYPE' THEN 'Usage Type'
        WHEN dimension = 'INSTANCE_TYPE' THEN 'Instance Type'
        WHEN dimension = 'OPERATION' THEN 'Operation'
        WHEN dimension = 'PURCHASE_TYPE' THEN 'Purchase Type'
        WHEN dimension = 'AZ' THEN 'Availability Zone'
        WHEN dimension = 'RECORD_TYPE' THEN 'Record Type'
        WHEN dimension = 'OPERATING_SYSTEM' THEN 'Operating System'
        WHEN dimension = 'TENANCY' THEN 'Tenancy'
        WHEN dimension = 'SCOPE' THEN 'Scope'
        WHEN dimension = 'PLATFORM' THEN 'Platform'
        WHEN dimension = 'SUBSCRIPTION_ID' THEN 'Subscription ID'
        WHEN dimension = 'LEGAL_ENTITY_NAME' THEN 'Legal Entity'
        WHEN dimension = 'DEPLOYMENT_OPTION' THEN 'Deployment Option'
        WHEN dimension = 'DATABASE_ENGINE' THEN 'Database Engine'
        WHEN dimension = 'INSTANCE_TYPE_FAMILY' THEN 'Instance Family'
        WHEN dimension = 'BILLING_ENTITY' THEN 'Billing Entity'
        WHEN dimension = 'RESERVATION_ID' THEN 'Reservation ID'
        WHEN dimension = 'SAVINGS_PLAN_ARN' THEN 'Savings Plan ARN'
        ELSE dimension
    END AS dimension_name,
    -- Additional derived fields for enhanced analytics
    CAST(upperbound - lowerbound AS decimal(18,4)) AS forecast_variance,
    CASE 
        WHEN meanvalue = 0 THEN 0
        ELSE CAST(((upperbound - lowerbound) / meanvalue * 100) AS decimal(18,2))
    END AS confidence_percentage,
    CASE
        WHEN (upperbound - lowerbound) / NULLIF(meanvalue, 0) * 100 < 10 THEN 'High Confidence'
        WHEN (upperbound - lowerbound) / NULLIF(meanvalue, 0) * 100 < 25 THEN 'Medium Confidence'
        ELSE 'Low Confidence'
    END AS confidence_level,
    DATE_FORMAT(CAST(startdate AS date), '%Y-%m') AS forecast_month,
    CONCAT('Q', CAST(EXTRACT(QUARTER FROM CAST(startdate AS date)) AS VARCHAR), ' ', CAST(EXTRACT(YEAR FROM CAST(startdate AS date)) AS VARCHAR)) AS forecast_quarter,
    EXTRACT(YEAR FROM CAST(startdate AS date)) AS forecast_year
FROM ${forecast_table_name}
