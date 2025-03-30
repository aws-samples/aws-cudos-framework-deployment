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
        ELSE dimension
    END AS dimension_name
FROM ${forecast_table_name}
