-- Cost Forecast Service Breakdown View
-- Provides forecast data broken down by service

CREATE OR REPLACE VIEW ${athena_database_name}.cost_forecast_service_view AS
WITH latest_forecast AS (
  SELECT
    payer_id,
    MAX(date_parse(concat(year, month, day), '%Y%m%d')) as forecast_date
  FROM
    optimization_data.cost_explorer_forecast_data
  GROUP BY
    payer_id
),

-- Get top services by cost from historical data
top_services AS (
  SELECT
    line_item_product_code as service,
    SUM(line_item_unblended_cost) as total_cost
  FROM
    ${cur_table_name}
  WHERE
    line_item_usage_start_date >= DATE_ADD('month', -3, current_date)
  GROUP BY
    line_item_product_code
  ORDER BY
    total_cost DESC
  LIMIT 10
),

-- Get historical service costs
historical_service_costs AS (
  SELECT
    bill_payer_account_id as payer_id,
    DATE_TRUNC('month', line_item_usage_start_date) as month_date,
    'HISTORICAL' as data_type,
    line_item_product_code as service,
    'UNBLENDED_COST' as metric,
    SUM(line_item_unblended_cost) as cost,
    EXTRACT(year FROM line_item_usage_start_date) as year,
    EXTRACT(month FROM line_item_usage_start_date) as month
  FROM
    ${cur_table_name}
  WHERE
    line_item_usage_start_date >= DATE_ADD('month', -12, current_date)
  GROUP BY
    1, 2, 4, 5, 7, 8
),

-- Get forecast monthly data distribution by service
forecast_total AS (
  SELECT
    f.payer_id,
    DATE_TRUNC('month', date_parse(result.timeperiod.start, '%Y-%m-%d')) as month_date,
    SUM(CAST(result.meanvalue AS decimal(20,2))) as total_forecast_cost
  FROM
    optimization_data.cost_explorer_forecast_data f
    CROSS JOIN UNNEST(f.forecastresultsbytime) as t(result)
  JOIN
    latest_forecast l ON f.payer_id = l.payer_id
    AND date_parse(concat(f.year, f.month, f.day), '%Y%m%d') = l.forecast_date
  WHERE
    f.granularity IN ('MONTHLY')
  GROUP BY
    1, 2
),

-- Calculate service distribution ratios from historical data
service_distribution AS (
  SELECT
    h.payer_id,
    h.service,
    AVG(h.cost / t.total_historical_cost) as distribution_ratio
  FROM
    historical_service_costs h
  JOIN (
    SELECT
      payer_id,
      month_date,
      SUM(cost) as total_historical_cost
    FROM
      historical_service_costs
    GROUP BY
      payer_id, month_date
  ) t ON h.payer_id = t.payer_id AND h.month_date = t.month_date
  GROUP BY
    1, 2
),

-- Apply distribution ratios to forecast data to estimate service-level forecasts
forecast_services AS (
  SELECT
    f.payer_id,
    f.month_date,
    'FORECAST' as data_type,
    s.service,
    'UNBLENDED_COST' as metric,
    f.total_forecast_cost * s.distribution_ratio as cost,
    EXTRACT(year FROM f.month_date) as year,
    EXTRACT(month FROM f.month_date) as month
  FROM
    forecast_total f
  JOIN
    service_distribution s ON f.payer_id = s.payer_id
)

-- Combine historical and forecasted service data
SELECT
  payer_id,
  month_date,
  data_type,
  service,
  metric,
  cost,
  year,
  month
FROM (
  SELECT * FROM historical_service_costs
  UNION ALL
  SELECT * FROM forecast_services
) combined
WHERE service IN (SELECT service FROM top_services)
ORDER BY
  payer_id, service, month_date;
