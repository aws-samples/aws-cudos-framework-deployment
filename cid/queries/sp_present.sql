SELECT
  identity_line_item_id
FROM
  "${cur_table_name}"
WHERE
  savings_plan_savings_plan_a_r_n NOT LIKE ''
LIMIT 10
