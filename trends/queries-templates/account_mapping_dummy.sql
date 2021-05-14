CREATE OR REPLACE VIEW aws_accounts AS
SELECT DISTINCT
    "line_item_usage_account_id" "account_id", "bill_payer_account_id" "parent_account_id", 'Active' "account_status", "line_item_usage_account_id" "account_name"
FROM
    ${athena_cur_table_name}
