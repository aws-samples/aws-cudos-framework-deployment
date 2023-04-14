CREATE OR REPLACE VIEW ${athena_view_name} AS
SELECT
   *
FROM
   ( VALUES ${rows} )
ignored_table_name (account_id, account_name, parent_account_id, account_status)