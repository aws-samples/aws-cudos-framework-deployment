CREATE OR REPLACE VIEW compute_optimizer_auto_scale_options AS
SELECT *
FROM
  (
   SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , autoscalinggrouparn arn
   , TRY("split_part"(autoscalinggrouparn, ':', 4)) region
   , TRY("split_part"(autoscalinggrouparn, ':', 3)) service
   , autoscalinggroupname name
   , 'auto_scale' module
   , 'auto_scale' recommendationsourcetype
   , finding finding
   , CAST(null AS varchar(1)) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CONCAT(inferredworkloadtypes, ';', effectiverecommendationpreferencesenhancedinfrastructuremetrics) ressouce_details
   , CONCAT(utilizationmetrics_disk_read_bytes_per_second_maximum, ';', utilizationmetrics_disk_read_ops_per_second_maximum, ';', utilizationmetrics_disk_write_bytes_per_second_maximum, ';', utilizationmetrics_disk_write_ops_per_second_maximum, ';', utilizationmetrics_ebs_read_bytes_per_second_maximum, ';', utilizationmetrics_ebs_read_ops_per_second_maximum, ';', utilizationmetrics_ebs_write_bytes_per_second_maximum, ';', utilizationmetrics_ebs_write_ops_per_second_maximum, ';', utilizationmetrics_network_in_bytes_per_second_maximum, ';', utilizationmetrics_network_out_bytes_per_second_maximum, ';', utilizationmetrics_network_packets_in_per_second_maximum, ';', utilizationmetrics_network_packets_out_per_second_maximum, ';') utilizationmetrics
   , 'Current' option_name
   , currentconfiguration_instancetype option_from
   , '' option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , TRY((CAST(current_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(current_ondemandprice AS double)) hourlyprice
   , 0E0 estimatedmonthlysavings_value
   , 0E0 estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low') OR (recommendationoptions_1_migrationeffort = 'Medium')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low') OR (recommendationoptions_2_migrationeffort = 'Medium')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low') OR (recommendationoptions_3_migrationeffort = 'Medium')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(currentperformancerisk, 'na'), ';', COALESCE(currentconfiguration_instancetype, 'na'), ';', '', ';', COALESCE(current_memory, 'na'), ';', COALESCE(current_vcpus, 'na'), ';', COALESCE(current_network, 'na'), ';', COALESCE(current_storage, 'na'), ';', '', ';', COALESCE(utilizationmetrics_cpu_maximum, 'na'), ';', COALESCE(utilizationmetrics_memory_maximum, 'na'), ';', COALESCE(currentconfiguration_desiredcapacity, 'na'), ';') option_details
   , CAST(null AS varchar(1)) tags
   FROM
     compute_optimizer_auto_scale_lines
   WHERE (autoscalinggrouparn LIKE '%arn:%')
UNION    SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , autoscalinggrouparn arn
   , TRY("split_part"(autoscalinggrouparn, ':', 4)) region
   , TRY("split_part"(autoscalinggrouparn, ':', 3)) service
   , autoscalinggroupname name
   , 'auto_scale' module
   , 'auto_scale' recommendationsourcetype
   , finding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CONCAT(inferredworkloadtypes, ';', effectiverecommendationpreferencesenhancedinfrastructuremetrics) ressouce_details
   , CONCAT(COALESCE(utilizationmetrics_disk_read_bytes_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_disk_read_ops_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_disk_write_bytes_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_disk_write_ops_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_ebs_read_bytes_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_ebs_read_ops_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_ebs_write_bytes_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_ebs_write_ops_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_network_in_bytes_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_network_out_bytes_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_network_packets_in_per_second_maximum, 'na'), ';', COALESCE(utilizationmetrics_network_packets_out_per_second_maximum, 'na')) option_details
   , 'Option 1' option_name
   , currentconfiguration_instancetype option_from
   , recommendationoptions_1_configuration_instancetype option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , TRY((CAST(recommendationoptions_1_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(recommendationoptions_1_ondemandprice AS double)) hourlyprice
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) estimatedmonthlysavings_value
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low') OR (recommendationoptions_1_migrationeffort = 'Medium')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low') OR (recommendationoptions_2_migrationeffort = 'Medium')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low') OR (recommendationoptions_3_migrationeffort = 'Medium')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(recommendationoptions_1_performancerisk, 'na'), ';', COALESCE(recommendationoptions_1_configuration_instancetype, 'na'), ';', COALESCE(recommendationoptions_1_migrationeffort, 'na'), ';', COALESCE(recommendationoptions_1_memory, 'na'), ';', COALESCE(recommendationoptions_1_vcpus, 'na'), ';', COALESCE(recommendationoptions_1_network, 'na'), ';', COALESCE(recommendationoptions_1_storage, 'na'), ';', 'na', ';', COALESCE(recommendationoptions_1_projectedutilizationmetrics_cpu_maximum, 'na'), ';', COALESCE(recommendationoptions_1_projectedutilizationmetrics_memory_maximum, 'na'), ';', COALESCE(recommendationoptions_1_configuration_desiredcapacity, 'na')) option_details
   , CAST(null AS varchar(1)) tags
   FROM
     compute_optimizer_auto_scale_lines
   WHERE ((autoscalinggrouparn LIKE '%arn:%') AND (recommendationoptions_2_estimatedmonthlysavings_currency <> ''))
UNION    SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , autoscalinggrouparn arn
   , TRY("split_part"(autoscalinggrouparn, ':', 4)) region
   , TRY("split_part"(autoscalinggrouparn, ':', 3)) service
   , autoscalinggroupname name
   , 'auto_scale' module
   , 'auto_scale' recommendationsourcetype
   , finding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CONCAT(inferredworkloadtypes, ';', effectiverecommendationpreferencesenhancedinfrastructuremetrics) ressouce_details
   , CONCAT(utilizationmetrics_disk_read_bytes_per_second_maximum, ';', utilizationmetrics_disk_read_ops_per_second_maximum, ';', utilizationmetrics_disk_write_bytes_per_second_maximum, ';', utilizationmetrics_disk_write_ops_per_second_maximum, ';', utilizationmetrics_ebs_read_bytes_per_second_maximum, ';', utilizationmetrics_ebs_read_ops_per_second_maximum, ';', utilizationmetrics_ebs_write_bytes_per_second_maximum, ';', utilizationmetrics_ebs_write_ops_per_second_maximum, ';', utilizationmetrics_network_in_bytes_per_second_maximum, ';', utilizationmetrics_network_out_bytes_per_second_maximum, ';', utilizationmetrics_network_packets_in_per_second_maximum, ';', utilizationmetrics_network_packets_out_per_second_maximum, ';') utilizationmetrics
   , 'Option 2' option_name
   , currentconfiguration_instancetype option_from
   , recommendationoptions_2_configuration_instancetype option_to
   , recommendationoptions_2_estimatedmonthlysavings_currency currency
   , TRY((CAST(recommendationoptions_2_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(recommendationoptions_2_ondemandprice AS double)) hourlyprice
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) estimatedmonthlysavings_value
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low') OR (recommendationoptions_1_migrationeffort = 'Medium')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low') OR (recommendationoptions_2_migrationeffort = 'Medium')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low') OR (recommendationoptions_3_migrationeffort = 'Medium')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(recommendationoptions_2_performancerisk, 'na'), ';', COALESCE(recommendationoptions_2_configuration_instancetype, 'na'), ';', COALESCE(recommendationoptions_2_migrationeffort, 'na'), ';', COALESCE(recommendationoptions_2_memory, 'na'), ';', COALESCE(recommendationoptions_2_vcpus, 'na'), ';', COALESCE(recommendationoptions_2_network, 'na'), ';', COALESCE(recommendationoptions_2_storage, 'na'), ';', 'na', ';', COALESCE(recommendationoptions_2_projectedutilizationmetrics_cpu_maximum, 'na'), ';', COALESCE(recommendationoptions_2_projectedutilizationmetrics_memory_maximum, 'na'), ';', COALESCE(recommendationoptions_2_configuration_desiredcapacity, 'na')) option_details
   , CAST(null AS varchar(1)) tags
   FROM
     compute_optimizer_auto_scale_lines
   WHERE ((autoscalinggrouparn LIKE '%arn:%') AND (recommendationoptions_2_estimatedmonthlysavings_currency <> ''))
UNION    SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , autoscalinggrouparn arn
   , TRY("split_part"(autoscalinggrouparn, ':', 4)) region
   , TRY("split_part"(autoscalinggrouparn, ':', 3)) service
   , autoscalinggroupname name
   , 'auto_scale' module
   , 'auto_scale' recommendationsourcetype
   , finding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CONCAT(inferredworkloadtypes, ';', effectiverecommendationpreferencesenhancedinfrastructuremetrics) ressouce_details
   , CONCAT(utilizationmetrics_disk_read_bytes_per_second_maximum, ';', utilizationmetrics_disk_read_ops_per_second_maximum, ';', utilizationmetrics_disk_write_bytes_per_second_maximum, ';', utilizationmetrics_disk_write_ops_per_second_maximum, ';', utilizationmetrics_ebs_read_bytes_per_second_maximum, ';', utilizationmetrics_ebs_read_ops_per_second_maximum, ';', utilizationmetrics_ebs_write_bytes_per_second_maximum, ';', utilizationmetrics_ebs_write_ops_per_second_maximum, ';', utilizationmetrics_network_in_bytes_per_second_maximum, ';', utilizationmetrics_network_out_bytes_per_second_maximum, ';', utilizationmetrics_network_packets_in_per_second_maximum, ';', utilizationmetrics_network_packets_out_per_second_maximum, ';') utilizationmetrics
   , 'Option 3' option_name
   , currentconfiguration_instancetype option_from
   , recommendationoptions_3_configuration_instancetype option_to
   , recommendationoptions_3_estimatedmonthlysavings_currency currency
   , TRY((CAST(recommendationoptions_3_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(recommendationoptions_3_ondemandprice AS double)) hourlyprice
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) estimatedmonthlysavings_value
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low') OR (recommendationoptions_1_migrationeffort = 'Medium')) AND (recommendationoptions_1_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low') OR (recommendationoptions_2_migrationeffort = 'Medium')) AND (recommendationoptions_2_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low') OR (recommendationoptions_3_migrationeffort = 'Medium')) AND (recommendationoptions_3_ondemandprice <> '')) THEN TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(recommendationoptions_3_performancerisk, 'na'), ';', COALESCE(recommendationoptions_3_configuration_instancetype, 'na'), ';', COALESCE(recommendationoptions_3_migrationeffort, 'na'), ';', COALESCE(recommendationoptions_3_memory, 'na'), ';', COALESCE(recommendationoptions_3_vcpus, 'na'), ';', COALESCE(recommendationoptions_3_network, 'na'), ';', COALESCE(recommendationoptions_3_storage, 'na'), ';', 'na', ';', COALESCE(recommendationoptions_3_projectedutilizationmetrics_cpu_maximum, 'na'), ';', COALESCE(recommendationoptions_3_projectedutilizationmetrics_memory_maximum, 'na'), ';', COALESCE(recommendationoptions_3_configuration_desiredcapacity, 'na')) option_details
   , CAST(null AS varchar(1)) tags
   FROM
     compute_optimizer_auto_scale_lines
   WHERE ((autoscalinggrouparn LIKE '%arn:%') AND (recommendationoptions_3_estimatedmonthlysavings_currency <> ''))
) 