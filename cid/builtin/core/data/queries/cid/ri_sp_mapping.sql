 <%doc>

# render this template:
python3 ./cid/render_template.py ./cid/builtin/core/data/queries/cid/ri_sp_mapping.sql \
   --cur_has_savings_plan True \
   --cur_has_reservations False \
   --cur_table_name customer_all

</%doc>

CREATE OR REPLACE VIEW "ri_sp_mapping" AS
SELECT DISTINCT
   "a"."billing_period_mapping"
 , "a"."payer_account_id_mapping"
 , "a"."ri_sp_arn_mapping"
 , "a"."ri_sp_end_date"
 , "b"."ri_sp_term"
 , "b"."ri_sp_offering"
 , "b"."ri_sp_payment"
FROM
   ((
    SELECT DISTINCT
  "bill_billing_period_start_date" "billing_period_mapping"
 , "bill_payer_account_id" "payer_account_id_mapping"
 , CASE
%if cur_has_savings_plan:
    WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN "savings_plan_savings_plan_a_r_n"
%endif
%if cur_has_reservations:
    WHEN ("reservation_reservation_a_r_n" <> '') THEN "reservation_reservation_a_r_n"
%endif
%if not cur_has_reservations and not cur_has_savings_plan:
    WHEN ("line_item_line_item_type" = 'Usage') THEN ' '
%endif
    ELSE ''
   END "ri_sp_arn_mapping"
 , CAST(CASE
%if cur_has_savings_plan:
    WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN CAST(from_iso8601_timestamp("savings_plan_end_time") AS timestamp)
%endif
%if cur_has_reservations:
    WHEN ("reservation_reservation_a_r_n" <> '' AND "reservation_end_time" <> '') THEN CAST(from_iso8601_timestamp("reservation_end_time") AS timestamp) 
%endif
%if not cur_has_reservations and not cur_has_savings_plan:
    WHEN ("line_item_line_item_type" = 'Usage') THEN ' '
%endif
    ELSE NULL
   END AS timestamp) "ri_sp_end_date"
    FROM
     "${cur_table_name}"
 WHERE (
%if not cur_has_reservations and not cur_has_savings_plan:
    ("line_item_line_item_type" <> 'Usage')
%else:
    FALSE
%endif
%if cur_has_reservations:
    OR ("line_item_line_item_type" = 'RIFee')
%endif
%if cur_has_savings_plan:
    OR ("line_item_line_item_type" = 'SavingsPlanRecurringFee')
%endif
 )
)  a
LEFT JOIN (
 SELECT DISTINCT
  "bill_billing_period_start_date" "billing_period_mapping"
 , "bill_payer_account_id" "payer_account_id_mapping"
 , CASE
%if cur_has_savings_plan:
   WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN "savings_plan_savings_plan_a_r_n"
%endif
%if cur_has_reservations:
   WHEN ("reservation_reservation_a_r_n" <> '') THEN "reservation_reservation_a_r_n"
%endif
%if not cur_has_reservations and not cur_has_savings_plan:
   WHEN ("line_item_line_item_type" = 'Usage') THEN ' '
%endif
   ELSE ''
 END "ri_sp_arn_mapping"
 , CASE
%if cur_has_savings_plan:
   WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN "savings_plan_purchase_term"
%endif
%if cur_has_reservations:
   WHEN ("reservation_reservation_a_r_n" <> '') THEN "pricing_lease_contract_length"
%endif
%if not cur_has_reservations and not cur_has_savings_plan:
     WHEN ("line_item_line_item_type" = 'Usage') THEN ' '
%endif
 ELSE '' END "ri_sp_term"
 , CASE
%if cur_has_savings_plan:
   WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN "savings_plan_offering_type"
%endif
%if cur_has_reservations:
   WHEN ("reservation_reservation_a_r_n" <> '') THEN "pricing_offering_class"
%endif
%if not cur_has_reservations and not cur_has_savings_plan:
   WHEN ("line_item_line_item_type" = 'Usage') THEN ' '
%endif
   ELSE ''
 END "ri_sp_offering"
 , CASE
%if cur_has_savings_plan:
   WHEN ("savings_plan_savings_plan_a_r_n" <> '') THEN "savings_plan_payment_option"
%endif
%if cur_has_reservations:
   WHEN ("reservation_reservation_a_r_n" <> '') THEN "pricing_purchase_option"
%endif
%if not cur_has_reservations and not cur_has_savings_plan:
   WHEN ("line_item_line_item_type" = 'Usage') THEN ' '
%endif
   ELSE ''
 END "ri_sp_Payment"
 FROM
      "${cur_table_name}"
 WHERE (
%if not cur_has_reservations and not cur_has_savings_plan:
    ("line_item_line_item_type" <> 'Usage')
%else:
    FALSE
%endif
%if cur_has_reservations:
  OR ("line_item_line_item_type" = 'DiscountedUsage')
%endif
%if cur_has_savings_plan:
  OR ("line_item_line_item_type" = 'SavingsPlanCoveredUsage')
%endif
 )
) b
ON (("a"."ri_sp_arn_mapping" = "b"."ri_sp_arn_mapping")
   AND ("a"."billing_period_mapping" = "b"."billing_period_mapping")
   AND ("a"."payer_account_id_mapping" = "b"."payer_account_id_mapping")
 )
)