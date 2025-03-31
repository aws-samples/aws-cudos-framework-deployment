CREATE OR REPLACE VIEW account_map AS 
select
  line_item_usage_account_id account_id
, MAX_BY(bill_payer_account_id, line_item_usage_start_date) parent_account_id
, MAX_BY(line_item_usage_account_id, line_item_usage_start_date) account_name
, MAX_BY(line_item_usage_account_id, line_item_usage_start_date) account_email_id
from cur2
group by 1
