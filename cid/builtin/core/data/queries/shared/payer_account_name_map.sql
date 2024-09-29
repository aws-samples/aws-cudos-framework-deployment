CREATE OR REPLACE VIEW payer_account_name_map AS
SELECT
  "account_id"
, "account_name" "payer_account_name"
FROM
  aws_accounts
WHERE ("parent_account_id" = "account_id")