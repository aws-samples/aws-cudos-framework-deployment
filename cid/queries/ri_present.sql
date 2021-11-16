SELECT
  identity_line_item_id
FROM
  ${cur_table_name}
WHERE
  reservation_start_time NOT LIKE ''
LIMIT 10
