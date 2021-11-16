 CREATE OR REPLACE VIEW "compute_savings_plan_eligible_spend" AS 
 SELECT DISTINCT
 "year"
 , "month"
 , "bill_payer_account_id" "payer_account_id"
 , "line_item_usage_account_id" "linked_account_id"
 , "bill_billing_period_start_date" "billing_period"
 , "date_trunc"('hour', "line_item_usage_start_date") "usage_date"
 , "sum"(CASE
     WHEN (((("line_item_line_item_type" = 'Usage') AND (NOT ("line_item_usage_type" LIKE '%Spot%'))) AND ("product_servicecode" <> 'AWSDataTransfer')) AND ("line_item_usage_type" NOT LIKE '%DataXfer%')) THEN
         CASE
             WHEN (("line_item_product_code" = 'AmazonEC2') AND ("line_item_operation" LIKE '%RunInstances%')) THEN "line_item_unblended_cost"
             WHEN (("line_item_product_code" = 'AWSLambda') AND ("line_item_usage_type" LIKE '%Lambda-Provisioned-GB-Second%')) THEN "line_item_unblended_cost"
             WHEN (("line_item_product_code" = 'AWSLambda') AND ("line_item_usage_type" LIKE '%Lambda-GB-Second%')) THEN "line_item_unblended_cost"
             WHEN (("line_item_product_code" = 'AWSLambda') AND ("line_item_usage_type" LIKE '%Lambda-Provisioned-Concurrency%')) THEN "line_item_unblended_cost"
             WHEN ("line_item_usage_type" LIKE '%Fargate%') THEN "line_item_unblended_cost"
             ELSE 0
         END
     ELSE 0 
     END) "unblended_cost"
 FROM
    ${cur_table_name}
 WHERE (("bill_billing_period_start_date" >= ("date_trunc"('month', current_timestamp) - INTERVAL  '1' MONTH)) AND ("line_item_usage_start_date" < ("date_trunc"('day', current_timestamp) - INTERVAL  '1' DAY)) AND ((("line_item_product_code" = 'AmazonEC2') AND ("line_item_operation" LIKE '%RunInstances%')) OR (("line_item_product_code" = 'AWSLambda') AND ("line_item_usage_type" LIKE '%Lambda-Provisioned-GB-Second%')) OR (("line_item_product_code" = 'AWSLambda') AND ("line_item_usage_type" LIKE '%Lambda-GB-Second%')) OR (("line_item_product_code" = 'AWSLambda') AND ("line_item_usage_type" LIKE '%Lambda-Provisioned-Concurrency%')) OR ("line_item_usage_type" LIKE '%Fargate%')) AND ("line_item_line_item_type" = 'Usage') AND ("line_item_usage_type" NOT LIKE '%Spot%') AND ("product_servicecode" <> 'AWSDataTransfer') AND ("line_item_usage_type" NOT LIKE '%DataXfer%')) 
 GROUP BY 1, 2, 3, 4,5,6
