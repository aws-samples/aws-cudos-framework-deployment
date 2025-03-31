CREATE EXTERNAL TABLE `compute_optimizer_lambda_lines`(
  `accountid` string COMMENT 'from deserializer', 
  `functionarn` string COMMENT 'from deserializer', 
  `functionversion` string COMMENT 'from deserializer', 
  `finding` string COMMENT 'from deserializer', 
  `findingreasoncodes_ismemoryoverprovisioned` string COMMENT 'from deserializer', 
  `findingreasoncodes_ismemoryunderprovisioned` string COMMENT 'from deserializer', 
  `findingreasoncodes_isinsufficientdata` string COMMENT 'from deserializer', 
  `findingreasoncodes_isinconclusive` string COMMENT 'from deserializer', 
  `numberofinvocations` string COMMENT 'from deserializer', 
  `lookbackperiodindays` string COMMENT 'from deserializer', 
  `lastrefreshtimestamp_utc` string COMMENT 'from deserializer', 
  `currentconfiguration_memorysize` string COMMENT 'from deserializer', 
  `currentconfiguration_timeout` string COMMENT 'from deserializer', 
  `current_costtotal` string COMMENT 'from deserializer', 
  `current_costaverage` string COMMENT 'from deserializer', 
  `recommendations_count` string COMMENT 'from deserializer', 
  `recommendationoptions_1_configuration_memorysize` string COMMENT 'from deserializer', 
  `recommendationoptions_1_costlow` string COMMENT 'from deserializer', 
  `recommendationoptions_1_costhigh` string COMMENT 'from deserializer', 
  `recommendationoptions_1_projectedutilizationmetrics_durationlowerbound` string COMMENT 'from deserializer', 
  `recommendationoptions_1_projectedutilizationmetrics_durationupperbound` string COMMENT 'from deserializer', 
  `recommendationoptions_1_projectedutilizationmetrics_durationexpected` string COMMENT 'from deserializer', 
  `recommendationoptions_2_configuration_memorysize` string COMMENT 'from deserializer', 
  `recommendationoptions_2_costlow` string COMMENT 'from deserializer', 
  `recommendationoptions_2_costhigh` string COMMENT 'from deserializer', 
  `recommendationoptions_2_projectedutilizationmetrics_durationlowerbound` string COMMENT 'from deserializer', 
  `recommendationoptions_2_projectedutilizationmetrics_durationupperbound` string COMMENT 'from deserializer', 
  `recommendationoptions_2_projectedutilizationmetrics_durationexpected` string COMMENT 'from deserializer', 
  `recommendationoptions_3_configuration_memorysize` string COMMENT 'from deserializer', 
  `recommendationoptions_3_costlow` string COMMENT 'from deserializer', 
  `recommendationoptions_3_costhigh` string COMMENT 'from deserializer', 
  `recommendationoptions_3_projectedutilizationmetrics_durationlowerbound` string COMMENT 'from deserializer', 
  `recommendationoptions_3_projectedutilizationmetrics_durationupperbound` string COMMENT 'from deserializer', 
  `recommendationoptions_3_projectedutilizationmetrics_durationexpected` string COMMENT 'from deserializer', 
  `utilizationmetrics_durationmaximum` string COMMENT 'from deserializer', 
  `utilizationmetrics_memorymaximum` string COMMENT 'from deserializer', 
  `utilizationmetrics_durationaverage` string COMMENT 'from deserializer', 
  `utilizationmetrics_memoryaverage` string COMMENT 'from deserializer', 
  `currentperformancerisk` string COMMENT 'from deserializer', 
  `recommendationoptions_1_savingsopportunitypercentage` string COMMENT 'from deserializer', 
  `recommendationoptions_1_estimatedmonthlysavings_currency` string COMMENT 'from deserializer', 
  `recommendationoptions_1_estimatedmonthlysavings_value` string COMMENT 'from deserializer', 
  `recommendationoptions_2_savingsopportunitypercentage` string COMMENT 'from deserializer', 
  `recommendationoptions_2_estimatedmonthlysavings_currency` string COMMENT 'from deserializer', 
  `recommendationoptions_2_estimatedmonthlysavings_value` string COMMENT 'from deserializer', 
  `recommendationoptions_3_savingsopportunitypercentage` string COMMENT 'from deserializer', 
  `recommendationoptions_3_estimatedmonthlysavings_currency` string COMMENT 'from deserializer', 
  `recommendationoptions_3_estimatedmonthlysavings_value` string COMMENT 'from deserializer')
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.serde2.OpenCSVSerde' 
WITH SERDEPROPERTIES ( 
  'quoteChar'='\"', 
  'separatorChar'=',') 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://data-bucket/compute_optimizer/compute_optimizer_lambda'
TBLPROPERTIES (
  'skip.header.line.count'='1')