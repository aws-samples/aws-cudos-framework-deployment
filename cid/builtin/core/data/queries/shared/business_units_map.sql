CREATE VIEW business_units_map AS
SELECT *
FROM
  (
 VALUES
     ROW ('111111111', 'account1', 'Business Unit 1')
   , ROW ('222222222', 'account2', 'Business Unit 2')
)  ignored_table_name (account_id, account_name, bu)