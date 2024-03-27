CREATE OR REPLACE VIEW account_map AS
SELECT 
    ${account_id} AS account_id,
    (CASE 
        WHEN  ${account_name} <> '' 
        THEN MAX_BY(concat(${account_name}, ': ', ${account_id}), concat(${account_name}, ': ', ${account_id})) 
        ELSE ${account_id} 
    END) AS account_name
FROM 
   ${metadata_table_name}
GROUP BY 
   ${account_id}
