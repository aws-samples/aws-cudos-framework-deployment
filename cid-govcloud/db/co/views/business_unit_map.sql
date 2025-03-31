-- development
CREATE VIEW business_units_map AS
SELECT *
FROM
  (
 VALUES 
     ROW ('111111111', 'account1', 'Business Unit 1')
   , ROW ('222222222', 'account2', 'Business Unit 2')
)  ignored_table_name (account_id, account_name, bu)

-- production
CREATE OR REPLACE VIEW "business_units_map" AS 
SELECT
  A.id account_id
, A.name account_name
, (CASE WHEN ((B.portfolio = '0') OR (B.portfolio = '#N/A') OR (B.portfolio = 'Not Accepted by PLM')) THEN 'Workload Not Accepted by PLM' ELSE B.portfolio END) bu
, (CASE WHEN ((B.productline = '0') OR (B.productline = '#N/A') OR (B.productline = 'Not Accepted by PLM')) THEN 'Workload Not Accepted by PLM' ELSE B.productline END) prodline
FROM
  (accounts A
LEFT JOIN portfolio_product_line_vaec B ON (A.id = B.awsaccountnumber))
WHERE ((A.year = '2024') AND (A.month = '08') AND (A.day = '15'))
