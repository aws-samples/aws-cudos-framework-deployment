CREATE EXTERNAL TABLE `compute_optimizer_ebs_volume_lines`(
  `accountid` string COMMENT 'from deserializer', 
  `volumearn` string COMMENT 'from deserializer', 
  `finding` string COMMENT 'from deserializer', 
  `lookbackperiodindays` string COMMENT 'from deserializer', 
  `lastrefreshtimestamp_utc` string COMMENT 'from deserializer', 
  `currentconfiguration_volumetype` string COMMENT 'from deserializer', 
  `currentconfiguration_volumesize` string COMMENT 'from deserializer', 
  `currentconfiguration_volumebaselineiops` string COMMENT 'from deserializer', 
  `currentconfiguration_volumebaselinethroughput` string COMMENT 'from deserializer', 
  `currentconfiguration_volumeburstiops` string COMMENT 'from deserializer', 
  `currentconfiguration_volumeburstthroughput` string COMMENT 'from deserializer', 
  `current_monthlyprice` string COMMENT 'from deserializer', 
  `recommendations_count` string COMMENT 'from deserializer', 
  `recommendationoptions_1_configuration_volumetype` string COMMENT 'from deserializer', 
  `recommendationoptions_1_configuration_volumesize` string COMMENT 'from deserializer', 
  `recommendationoptions_1_configuration_volumebaselineiops` string COMMENT 'from deserializer', 
  `recommendationoptions_1_configuration_volumebaselinethroughput` string COMMENT 'from deserializer', 
  `recommendationoptions_1_configuration_volumeburstiops` string COMMENT 'from deserializer', 
  `recommendationoptions_1_configuration_volumeburstthroughput` string COMMENT 'from deserializer', 
  `recommendationoptions_1_monthlyprice` string COMMENT 'from deserializer', 
  `recommendationoptions_1_performancerisk` string COMMENT 'from deserializer', 
  `recommendationoptions_2_configuration_volumetype` string COMMENT 'from deserializer', 
  `recommendationoptions_2_configuration_volumesize` string COMMENT 'from deserializer', 
  `recommendationoptions_2_configuration_volumebaselineiops` string COMMENT 'from deserializer', 
  `recommendationoptions_2_configuration_volumebaselinethroughput` string COMMENT 'from deserializer', 
  `recommendationoptions_2_configuration_volumeburstiops` string COMMENT 'from deserializer', 
  `recommendationoptions_2_configuration_volumeburstthroughput` string COMMENT 'from deserializer', 
  `recommendationoptions_2_monthlyprice` string COMMENT 'from deserializer', 
  `recommendationoptions_2_performancerisk` string COMMENT 'from deserializer', 
  `recommendationoptions_3_configuration_volumetype` string COMMENT 'from deserializer', 
  `recommendationoptions_3_configuration_volumesize` string COMMENT 'from deserializer', 
  `recommendationoptions_3_configuration_volumebaselineiops` string COMMENT 'from deserializer', 
  `recommendationoptions_3_configuration_volumebaselinethroughput` string COMMENT 'from deserializer', 
  `recommendationoptions_3_configuration_volumeburstiops` string COMMENT 'from deserializer', 
  `recommendationoptions_3_configuration_volumeburstthroughput` string COMMENT 'from deserializer', 
  `recommendationoptions_3_monthlyprice` string COMMENT 'from deserializer', 
  `recommendationoptions_3_performancerisk` string COMMENT 'from deserializer', 
  `utilizationmetrics_volumereadopspersecondmaximum` string COMMENT 'from deserializer', 
  `utilizationmetrics_volumewriteopspersecondmaximum` string COMMENT 'from deserializer', 
  `utilizationmetrics_volumereadbytespersecondmaximum` string COMMENT 'from deserializer', 
  `utilizationmetrics_volumewritebytespersecondmaximum` string COMMENT 'from deserializer', 
  `errorcode` string COMMENT 'from deserializer', 
  `errormessage` string COMMENT 'from deserializer', 
  `currentperformancerisk` string COMMENT 'from deserializer', 
  `recommendationoptions_1_savingsopportunitypercentage` string COMMENT 'from deserializer', 
  `recommendationoptions_1_estimatedmonthlysavings_currency` string COMMENT 'from deserializer', 
  `recommendationoptions_1_estimatedmonthlysavings_value` string COMMENT 'from deserializer', 
  `recommendationoptions_2_savingsopportunitypercentage` string COMMENT 'from deserializer', 
  `recommendationoptions_2_estimatedmonthlysavings_currency` string COMMENT 'from deserializer', 
  `recommendationoptions_2_estimatedmonthlysavings_value` string COMMENT 'from deserializer', 
  `recommendationoptions_3_savingsopportunitypercentage` string COMMENT 'from deserializer', 
  `recommendationoptions_3_estimatedmonthlysavings_currency` string COMMENT 'from deserializer', 
  `recommendationoptions_3_estimatedmonthlysavings_value` string COMMENT 'from deserializer', 
  `currentconfiguration_rootvolume` string COMMENT 'from deserializer', 
  `tags` string COMMENT 'from deserializer')
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
  's3://data-bucket/compute_optimizer/compute_optimizer_ebs_volume'
TBLPROPERTIES (
  'skip.header.line.count'='1')