CREATE OR REPLACE VIEW aws_accounts AS WITH m AS (
        SELECT account_id,
            account_name,
            email account_email_id
        FROM ${metadata_table_name}
    ),
    cur AS (
        SELECT DISTINCT line_item_usage_account_id,
            bill_payer_account_id parent_account_id
        FROM ${cur_table_name}
    )
SELECT m.account_id,
    m.account_name,
    cur.parent_account_id,
    m.account_email_id,
    'Active' account_status
FROM (
        m
        LEFT JOIN cur ON m.account_id = cur.line_item_usage_account_id
    )
