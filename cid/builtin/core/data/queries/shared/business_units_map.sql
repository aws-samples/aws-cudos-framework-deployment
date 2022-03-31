CREATE VIEW business_units_map AS
SELECT *
FROM
  (
 VALUES
     ROW ('111111111', 'Business Unit 1')
   , ROW ('222222222', 'Business Unit 1')
)  ignored_table_name (account_id, bu)