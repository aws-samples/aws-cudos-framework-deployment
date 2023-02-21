CREATE OR REPLACE VIEW ${athena_view_name} AS
SELECT DISTINCT
    line_item_usage_account_id                                     account_id,
    MAX_BY(line_item_usage_account_id, line_item_usage_start_date) account_name,
    MAX_BY(bill_payer_account_id,      line_item_usage_start_date) parent_account_id,
    CAST('' AS varchar)                                            account_status,
    CAST('' AS varchar)                                            account_email,
    CAST('' AS varchar)                                            account_email_id
FROM
    "${cur_table_name}"
WHERE
    line_item_usage_account_id <> ''
GROUP BY
    line_item_usage_account_id