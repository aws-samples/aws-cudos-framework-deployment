CREATE OR REPLACE VIEW monthly_bill_by_account AS
WITH
  t1 AS (
   SELECT
     "bill_billing_period_start_date"
   , "bill_payer_account_id"
   , "line_item_usage_account_id"
   , "line_item_line_item_type" "charge_type"
   , (CASE WHEN ("product_product_name" LIKE '') THEN "line_item_product_code" ELSE "product_product_name" END) "product_product_name"
   , "product_region"
   , "line_item_product_code"
   , "round"("sum"("line_item_unblended_cost"), 2) "unblended_cost"
   , "round"(sum("line_item_unblended_cost") , 2) "amortized_cost"
   FROM
     "${cur_table_name}"
   GROUP BY 1, 2, 3, 4, 5, 6, 7
)
, t2 AS (
   SELECT
     "account_name"
   , "account_id"
   FROM
     aws_accounts
)
, t3 AS (
   SELECT
     "payer_account_name"
   , "account_id"
   FROM
     payer_account_name_map
)
, t4 AS (
   SELECT
     "region_latitude"
   , "region_longitude"
   , "region_name"
   FROM
     aws_regions
)
, t5 AS (
   SELECT
     "aws_service_category"
   , "line_item_product_code"
   FROM
     aws_service_category_map
)
SELECT
  t1.*
, "t2"."account_name"
, "t3"."payer_account_name"
, TRY_CAST("t4"."region_latitude" AS decimal) "region_latitude"
, TRY_CAST("t4"."region_longitude" AS decimal) "region_longitude"
, (CASE WHEN (("t5"."aws_service_category" IS NULL) AND ("t1"."product_product_name" IS NOT NULL)) THEN "t1"."product_product_name" WHEN (("aws_service_category" IS NULL) AND ("t1"."product_product_name" IS NULL)) THEN 'Other' ELSE "t5"."aws_service_category" END) "aws_service_category"
FROM
  ((((t1
LEFT JOIN t2 ON (CAST("t1"."line_item_usage_account_id" AS char(12)) = CAST("t2"."account_id" AS char(12))))
LEFT JOIN t3 ON (CAST("t1"."bill_payer_account_id" AS char(12)) = CAST("t3"."account_id" AS char(12))))
LEFT JOIN t4 ON ("t1"."product_region" = "t4"."region_name"))
LEFT JOIN t5 ON ("t1"."line_item_product_code" = "t5"."line_item_product_code"))