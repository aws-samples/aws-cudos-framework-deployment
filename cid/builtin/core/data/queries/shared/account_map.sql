CREATE OR REPLACE VIEW account_map AS
SELECT
    ${account_id} AS account_id,
    MAX_BY(${account_name}, ${account_id}) AS account_name
FROM
   "${metadata_database_name}"."${metadata_table_name}"
WHERE
   ${account_name} <> ''
GROUP BY
   ${account_id}
