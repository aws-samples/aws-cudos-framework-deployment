CREATE OR REPLACE VIEW s3_view AS 
select
    date_format(date_parse(billing_period, '%Y-%m'), '%Y') as year
    , regexp_replace(date_format(date_parse(billing_period, '%Y-%m'), '%m'), '^0', '') as month
    , date_parse(billing_period, '%Y-%m') as billing_period
    , date_trunc('day', line_item_usage_start_date) usage_date
    , bill_payer_account_id as payer_account_id
    , line_item_usage_account_id as linked_account_id
    , line_item_resource_id as resource_id
    , line_item_product_code as product_code
    , line_item_operation as operation
    , product_region_code as region
    , line_item_line_item_type as charge_type
    , pricing_unit
    , sum((CASE WHEN (line_item_line_item_type = 'Usage') THEN line_item_usage_amount ELSE 0 END)) as usage_quantity
    , sum(line_item_unblended_cost) as unblended_cost
    , sum(pricing_public_on_demand_cost) as public_cost
from cur2
WHERE ((bill_billing_period_start_date >= (date_trunc('month', current_timestamp) - INTERVAL '3' MONTH)) AND (line_item_usage_start_date < (date_trunc('day', current_timestamp) - INTERVAL '1' DAY))) AND (line_item_operation LIKE '%Storage%') AND ((line_item_product_code LIKE '%AmazonGlacier%') OR (line_item_product_code LIKE '%AmazonS3%'))
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
