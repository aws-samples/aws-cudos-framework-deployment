CREATE OR REPLACE VIEW account_map AS
SELECT ${account_id} as account_id,
    concat(${account_name}, ': ', ${account_id}) account_name
FROM ${metadata_table_name}
