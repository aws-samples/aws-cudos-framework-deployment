CREATE OR REPLACE VIEW "compute_optimizer_all_options" AS
WITH
  co_data AS (
   SELECT *
   ,"split_part"("substring"("arn", 1, ("length"("arn"))), '/', 2) "resource_id"
   FROM
     compute_optimizer_ec2_instance_options
UNION    SELECT *
   ,"split_part"("substring"("arn", 1, ("length"("arn"))), '/', 2) "resource_id"
   FROM
     compute_optimizer_ebs_volume_options
UNION    SELECT *
   ,"split_part"("substring"("arn", 1, ("length"("arn"))), '/', 2) "resource_id"
   FROM
     compute_optimizer_auto_scale_options
UNION    SELECT *
   ,"arn" "resource_id"
   FROM
     compute_optimizer_lambda_options
)
, tags as (
  SELECT DISTINCT
   line_item_resource_id AS resource_id,
   CONCAT(
     '{',
     ARRAY_JOIN(
      filter( 
        ARRAY[
%for tag in tags:
        CASE WHEN resource_tags_user_${tag} != '' THEN CONCAT('"${tag}":"', resource_tags_user_${tag}, '"') ELSE NULL END,
%endfor
        NULL
        ], el -> el is not NULL),
        ','
      ),
     '}'
    ) AS tags

    FROM
      customer_all
    WHERE (
      ("bill_billing_period_start_date" >= ("date_trunc"('month', current_timestamp) - INTERVAL  '01' MONTH)) AND (CAST("concat"("year", '-', "month", '-01') AS date) >= ("date_trunc"('month', current_date) - INTERVAL  '01' MONTH)))
      AND (    "line_item_product_code" = 'AmazonEC2' AND (line_item_resource_id like  'i-%'  OR line_item_resource_id like  'vol-%' )
            OR "line_item_product_code" = 'AWSLambda')
    )

(SELECT DISTINCT
  co_data.*
  tags
FROM
 (co_data
 LEFT JOIN tags ON (tags.resource_id = co_data.resource_id))
)
