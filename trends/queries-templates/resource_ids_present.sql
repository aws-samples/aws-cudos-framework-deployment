SELECT *
FROM information_schema.columns
WHERE table_name = '${athena_cur_table_name}'
    AND column_name = 'line_item_resource_id'
