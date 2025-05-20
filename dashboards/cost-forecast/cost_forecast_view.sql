-- Cost Forecast View for QuickSight Dashboard
-- This view combines historical data from CUR and forecast data from the optimization_data.cost_explorer_forecast_data table

-- Create a view for forecasted data that flattens the nested arrays and structs
CREATE OR REPLACE VIEW ${athena_database_name}.cost_forecast_view AS
WITH latest_forecast AS (
  SELECT
    payer_id,
    MAX(date_parse(concat(year, month, day), '%Y%m%d')) as forecast_date
  FROM
    optimization_data.cost_explorer_forecast_data
  GROUP BY
    payer_id
),

forecast_data AS (
  SELECT
    f.payer_id,
    result.timeperiod.start as forecast_date,
    date_parse(result.timeperiod.start, '%Y-%m-%d') as date,
    'FORECAST' as data_type,
    f.metric,
    CAST(result.meanvalue AS decimal(20,2)) as cost,
    CAST(result.predictionintervallowerbound AS decimal(20,2)) as lower_bound,
    CAST(result.predictionintervalupperbound AS decimal(20,2)) as upper_bound,
    f.predictionintervallevel as confidence_level,
    f.granularity,
    f.total.unit as currency_unit
  FROM
    optimization_data.cost_explorer_forecast_data f
    CROSS JOIN UNNEST(f.forecastresultsbytime) as t(result)
  JOIN
    latest_forecast l ON f.payer_id = l.payer_id
    AND date_parse(concat(f.year, f.month, f.day), '%Y%m%d') = l.forecast_date
),

-- Get historical data from CUR
historical_data AS (
  SELECT 
    bill_payer_account_id as payer_id,
    DATE_FORMAT(line_item_usage_start_date, '%Y-%m-%d') as historical_date,
    line_item_usage_start_date as date,
    'HISTORICAL' as data_type,
    'UNBLENDED_COST' as metric, -- Default to UNBLENDED_COST for historical
    SUM(line_item_unblended_cost) as cost,
    NULL as lower_bound,  -- No bounds for historical data
    NULL as upper_bound,
    NULL as confidence_level,
    CASE
      WHEN DATE_TRUNC('MONTH', line_item_usage_start_date) = DATE_TRUNC('MONTH', line_item_usage_end_date) THEN 'MONTHLY'
      ELSE 'DAILY'
    END as granularity,
    'USD' as currency_unit  -- Default currency, adjust if needed
  FROM
    ${cur_table_name}
  WHERE
    line_item_usage_start_date >= DATE_ADD('month', -3, current_date) -- Last 3 months
  GROUP BY
    1, 2, 3, 4, 5, 9, 10
)

-- Combine historical and forecast data
SELECT 
  payer_id,
  date,
  data_type,
  metric,
  cost,
  lower_bound,
  upper_bound,
  confidence_level,
  granularity,
  currency_unit
FROM 
  forecast_data

UNION ALL

SELECT 
  payer_id,
  date,
  data_type,
  metric,
  cost,
  lower_bound,
  upper_bound,
  confidence_level,
  granularity,
  currency_unit
FROM 
  historical_data
WHERE
  date < (SELECT MIN(date) FROM forecast_data); -- Only include historical data before forecast starts
