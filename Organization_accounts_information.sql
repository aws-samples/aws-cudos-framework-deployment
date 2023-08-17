CREATE OR REPLACE VIEW organization_accounts_information AS
SELECT *
FROM
(
VALUES
  ROW('117811442442', 'arn:aws:organizations::102756231718:account/o-b1y6mmnxm9/117811442442', 'gaborsch+optdatacoll@amazon.de', 'Optimization Data Collection', 'ACTIVE', 'INVITED', 'Wed Mar 08 2023 14:50:40 GMT+0100 (Central European Standard Time)')
, ROW('994076605136', 'arn:aws:organizations::102756231718:account/o-b1y6mmnxm9/994076605136', 'gaborsch+logarchive@amazon.de', 'Log Archive', 'ACTIVE', 'CREATED', 'Tue Nov 15 2022 14:52:57 GMT+0100 (Central European Standard Time)')
, ROW('874226311135', 'arn:aws:organizations::102756231718:account/o-b1y6mmnxm9/874226311135', 'gaborsch+optimization@amazon.de', 'OptimizationDataCollection', 'SUSPENDED', 'CREATED', 'Wed Mar 08 2023 13:33:40 GMT+0100 (Central European Standard Time)')
, ROW('102756231718', 'arn:aws:organizations::102756231718:account/o-b1y6mmnxm9/102756231718', 'gaborsch@amazon.de', 'TrainingAccount', 'ACTIVE', 'INVITED', 'Tue Nov 15 2022 14:37:43 GMT+0100 (Central European Standard Time)')
, ROW('713750282919', 'arn:aws:organizations::102756231718:account/o-b1y6mmnxm9/713750282919', 'gaborsch+audit@amazon.de', 'Audit', 'ACTIVE', 'CREATED', 'Tue Nov 15 2022 14:52:49 GMT+0100 (Central European Standard Time)')
) ignored_table_name (account_id, arn, email, name, status, joined_method, joined_timestamp)