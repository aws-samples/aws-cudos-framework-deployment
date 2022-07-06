<%doc>

# render this template:
python3 ./cid/render_template.py ./cid/builtin/core/data/queries/cid/ec2_running_cost.sql \
   --cur_has_savings_plan True \
   --cur_has_reservations False \
   --cur_table_name customer_all

</%doc>
CREATE OR REPLACE VIEW "ec2_running_cost" AS
 SELECT DISTINCT
 "year"
 , "month"
 , "bill_billing_period_start_date" "billing_period"
 , "date_trunc"('hour', "line_item_usage_start_date") "usage_date"
 , "bill_payer_account_id" "payer_account_id"
 , "line_item_usage_account_id" "linked_account_id"
 , (CASE
%if cur_has_savings_plan:
      WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN 'SavingsPlan'
%endif
%if cur_has_reservations:
      WHEN ("reservation_reservation_a_r_n" <> '') THEN 'Reserved'
%endif
      WHEN ("line_item_usage_type" LIKE '%Spot%') THEN 'Spot'
      ELSE 'OnDemand'
   END) "purchase_option"
 , "sum"(CASE
%if cur_has_savings_plan:
      WHEN "line_item_line_item_type" = 'SavingsPlanCoveredUsage' THEN "savings_plan_savings_plan_effective_cost"
%endif
%if cur_has_reservations:
      WHEN "line_item_line_item_type" = 'DiscountedUsage' THEN "reservation_effective_cost"
%endif
      WHEN "line_item_line_item_type" = 'Usage' THEN "line_item_unblended_cost"
      ELSE 0
   END) "amortized_cost"
 , "round"("sum"("line_item_usage_amount"), 2) "usage_quantity"
 FROM
    "${cur_table_name}"
 WHERE (
   ( "bill_billing_period_start_date" >= ("date_trunc"('month', current_timestamp) - INTERVAL  '1' MONTH))
   AND ("line_item_product_code" = 'AmazonEC2')
   AND ("product_servicecode" <> 'AWSDataTransfer')
   AND ("line_item_operation" LIKE '%RunInstances%')
   AND ("line_item_usage_type" NOT LIKE '%DataXfer%')
   AND (
     ("line_item_line_item_type" = 'Usage')
%if cur_has_savings_plan:
      OR ("line_item_line_item_type" = 'SavingsPlanCoveredUsage')
%endif
%if cur_has_reservations:
      OR ("line_item_line_item_type" = 'DiscountedUsage')
%endif
   )
 )
 GROUP BY 1,2,3,4,5,6,7