-- Cost Forecast Trend Analysis View
-- Provides year-over-year and month-over-month comparisons

CREATE OR REPLACE VIEW ${athena_database_name}.cost_forecast_trend_view AS
WITH latest_forecast AS (
  SELECT
    payer_id,
    MAX(date_parse(concat(year, month, day), '%Y%m%d')) as forecast_date
  FROM
    optimization_data.cost_explorer_forecast_data
  GROUP BY
    payer_id
),

-- Get monthly forecast data
monthly_forecast AS (
  SELECT
    f.payer_id,
    DATE_TRUNC('month', date_parse(result.timeperiod.start, '%Y-%m-%d')) as month_date,
    'FORECAST' as data_type,
    f.metric,
    SUM(CAST(result.meanvalue AS decimal(20,2))) as cost,
    SUM(CAST(result.predictionintervallowerbound AS decimal(20,2))) as lower_bound,
    SUM(CAST(result.predictionintervalupperbound AS decimal(20,2))) as upper_bound,
    f.predictionintervallevel as confidence_level,
    f.granularity,
    f.total.unit as currency_unit,
    EXTRACT(year FROM date_parse(result.timeperiod.start, '%Y-%m-%d')) as year,
    EXTRACT(month FROM date_parse(result.timeperiod.start, '%Y-%m-%d')) as month
  FROM
    optimization_data.cost_explorer_forecast_data f
    CROSS JOIN UNNEST(f.forecastresultsbytime) as t(result)
  JOIN
    latest_forecast l ON f.payer_id = l.payer_id
    AND date_parse(concat(f.year, f.month, f.day), '%Y%m%d') = l.forecast_date
  WHERE
    f.granularity IN ('MONTHLY', 'DAILY')
  GROUP BY
    1, 2, 3, 4, 8, 9, 10, 11, 12
),

-- Get historical monthly data from CUR
historical_monthly AS (
  SELECT 
    bill_payer_account_id as payer_id,
    DATE_TRUNC('month', line_item_usage_start_date) as month_date,
    'HISTORICAL' as data_type,
    'UNBLENDED_COST' as metric,
    SUM(line_item_unblended_cost) as cost,
    NULL as lower_bound,
    NULL as upper_bound,
    NULL as confidence_level,
    'MONTHLY' as granularity,
    'USD' as currency_unit,
    EXTRACT(year FROM line_item_usage_start_date) as year,
    EXTRACT(month FROM line_item_usage_start_date) as month
  FROM
    ${cur_table_name}
  WHERE
    line_item_usage_start_date >= DATE_ADD('year', -1, current_date) -- Last year
  GROUP BY
    1, 2, 3, 4, 9, 10, 11, 12
),

-- Combine historical and forecast monthly data
combined_monthly AS (
  SELECT * FROM monthly_forecast
  UNION ALL
  SELECT * FROM historical_monthly
  WHERE month_date < (SELECT MIN(month_date) FROM monthly_forecast)
),

-- Calculate YoY and MoM changes
monthly_trends AS (
  SELECT
    current_month.*,
    prior_year.cost as prior_year_cost,
    prior_month.cost as prior_month_cost,
    CASE 
      WHEN prior_year.cost > 0 THEN (current_month.cost - prior_year.cost) / prior_year.cost * 100 
      ELSE NULL 
    END as yoy_percent_change,
    CASE 
      WHEN prior_month.cost > 0 THEN (current_month.cost - prior_month.cost) / prior_month.cost * 100 
      ELSE NULL 
    END as mom_percent_change,
    -- Determine if the forecast shows an anomaly (> 20% change from previous month)
    CASE
      WHEN current_month.data_type = 'FORECAST' AND prior_month.cost > 0 AND 
           ABS((current_month.cost - prior_month.cost) / prior_month.cost) > 0.2
      THEN true
      ELSE false
    END as is_anomaly
  FROM
    combined_monthly current_month
  LEFT JOIN
    combined_monthly prior_year ON
      current_month.payer_id = prior_year.payer_id AND
      current_month.year = prior_year.year + 1 AND
      current_month.month = prior_year.month AND
      current_month.metric = prior_year.metric
  LEFT JOIN
    combined_monthly prior_month ON
      current_month.payer_id = prior_month.payer_id AND
      ((current_month.year = prior_month.year AND current_month.month = prior_month.month + 1) OR
       (current_month.year = prior_month.year + 1 AND current_month.month = 1 AND prior_month.month = 12)) AND
      current_month.metric = prior_month.metric
)

SELECT
  payer_id,
  month_date,
  data_type,
  metric,
  cost,
  lower_bound,
  upper_bound,
  confidence_level,
  granularity,
  currency_unit,
  year,
  month,
  prior_year_cost,
  prior_month_cost,
  yoy_percent_change,
  mom_percent_change,
  is_anomaly
FROM
  monthly_trends
ORDER BY
  payer_id, month_date;
