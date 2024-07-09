CREATE OR REPLACE VIEW "compute_optimizer_rds_instance_options" AS 
(
   SELECT
     TRY("date_parse"(lastrefreshtimestamp, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp
   , accountid accountid
   , resourcearn arn
   , TRY("split_part"(resourcearn, ':', 4)) region
   , TRY("split_part"(resourcearn, ':', 3)) service
   , TRY("split_part"(resourcearn, ':', 7)) name
   , 'rds' module
   , 'rds' recommendationsourcetype
   , instancefinding finding
   , CONCAT((CASE WHEN (instancefindingreasoncodes_iscpuoverprovisioned = 'true') THEN 'CPU-Over ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_iscpuunderprovisioned = 'true') THEN 'CPU-Under ' ELSE '' END), (CASE WHEN (storagefindingreasoncodes_isebsvolumeiopsoverprovisioned = 'true') THEN 'DiskIOPS-Over ' ELSE '' END), (CASE WHEN (storagefindingreasoncodes_isebsvolumethroughputoverprovisioned = 'true') THEN 'DiskThroughput-Over ' ELSE '' END), (CASE WHEN (storagefindingreasoncodes_isebsvolumethroughputunderprovisioned = 'true') THEN 'DiskThroughput-Under ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isebsiopsoverprovisioned = 'true') THEN 'EBSIOPS-Over ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isebsthroughputoverprovisioned = 'true') THEN 'EBSThroughput-Over ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isebsthroughputunderprovisioned = 'true') THEN 'EBSThroughput-Under ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isnetworkbandwidthoverprovisioned = 'true') THEN 'NetworkBandwidth-Over ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isnetworkbandwidthunderprovisioned = 'true') THEN 'NetworkBandwidth-Under ' ELSE '' END)) reason
   , lookbackperiodindays lookbackperiodindays
   , '' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , effectiverecommendationpreferencesenhancedinfrastructuremetrics ressouce_details
   , CONCAT(utilizationmetricscpumaximum, ';', utilizationmetricsmemorymaximum, ';', utilizationmetricsebsvolumestoragespaceutilizationmaximum, ';', utilizationmetricsnetworkreceivethroughputmaximum, ';', utilizationmetricsnetworktransmitthroughputmaximum, ';', utilizationmetricsebsvolumereadiopsmaximum, ';', utilizationmetricsebsvolumewriteiopsmaximum, ';', utilizationmetricsebsvolumereadthroughputmaximum, ';', utilizationmetricsebsvolumewritethroughputmaximum, ';', utilizationmetricsdatabaseconnectionsmaximum, ';') utilizationmetrics
   , 'Current' option_name
   , currentdbinstanceclass option_from
   , '' option_to
   , instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency currency
   , TRY((CAST(current_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(current_ondemandprice AS double)) hourlyprice
   , 0E0 estimatedmonthlysavings_value
   , 0E0 estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low') OR (recommendationoptions_1_migrationeffort = 'Medium')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low') OR (recommendationoptions_2_migrationeffort = 'Medium')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low') OR (recommendationoptions_3_migrationeffort = 'Medium')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(currentperformancerisk, 'na'), ';', COALESCE(currentdbinstanceclass, 'na'), ';', COALESCE('', 'na'), ';', COALESCE(current_memory, 'na'), ';', COALESCE(current_vcpus, 'na'), ';', COALESCE(current_network, 'na'), ';', COALESCE(current_storage, 'na'), ';', COALESCE('', 'na'), ';', COALESCE(utilizationmetrics_cpu_maximum, 'na'), ';', COALESCE(utilizationmetrics_memory_maximum, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE (resourcearn LIKE '%arn:%')
UNION    SELECT
     TRY("date_parse"(lastrefreshtimestamp, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp
   , accountid accountid
   , resourcearn arn
   , TRY("split_part"(resourcearn, ':', 4)) region
   , TRY("split_part"(resourcearn, ':', 3)) service
   , TRY("split_part"(resourcearn, ':', 7)) name
   , 'rds' module
   , 'rds' recommendationsourcetype
   , instancefinding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , '' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , '' ressouce_details
   , '' utilizationmetrics
   , 'Option 1' option_name
   , currentdbinstanceclass option_from
   , recommendationoptions_1_instancetype option_to
   , instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency currency
   , TRY((CAST(recommendationoptions_1_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(recommendationoptions_1_ondemandprice AS double)) hourlyprice
   , TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low') OR (recommendationoptions_1_migrationeffort = 'Medium')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low') OR (recommendationoptions_2_migrationeffort = 'Medium')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low') OR (recommendationoptions_3_migrationeffort = 'Medium')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(recommendationoptions_1_performancerisk, 'na'), ';', COALESCE(recommendationoptions_1_instancetype, 'na'), ';', COALESCE(recommendationoptions_1_migrationeffort, 'na'), ';', COALESCE(recommendationoptions_1_memory, 'na'), ';', COALESCE(recommendationoptions_1_vcpus, 'na'), ';', COALESCE(recommendationoptions_1_network, 'na'), ';', COALESCE(recommendationoptions_1_storage, 'na'), ';', CONCAT((CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_isarchitecturedifferent, 'na') = 'true') THEN 'Architecture ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_ishypervisordifferent, 'na') = 'true') THEN 'Hypervisor ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_isinstancestoreavailabilitydifferent, 'na') = 'true') THEN 'InstanceStoreAvailability ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_isnetworkinterfacedifferent, 'na') = 'true') THEN 'NetworkInterface ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_isstorageinterfacedifferent, 'na') = 'true') THEN 'StorageInterface ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_isvirtualizationtypedifferent, 'na') = 'true') THEN 'VirtualizationType ' ELSE '' END)), ';', COALESCE(recommendationoptions_1_projectedutilizationmetrics_cpu_maximum, 'na'), ';', COALESCE(recommendationoptions_1_projectedutilizationmetrics_memory_maximum, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE (resourcearn LIKE '%arn:%')
UNION    SELECT
     TRY("date_parse"(lastrefreshtimestamp, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp
   , accountid accountid
   , resourcearn arn
   , TRY("split_part"(resourcearn, ':', 4)) region
   , TRY("split_part"(resourcearn, ':', 3)) service
   , TRY("split_part"(resourcearn, ':', 7)) name
   , 'rds' module
   , 'rds' recommendationsourcetype
   , instancefinding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , '' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , '' ressouce_details
   , '' utilizationmetrics
   , 'Option 2' option_name
   , currentdbinstanceclass option_from
   , recommendationoptions_2_instancetype option_to
   , recommendationoptions_2_estimatedmonthlysavings_currency currency
   , TRY((CAST(recommendationoptions_2_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(recommendationoptions_2_ondemandprice AS double)) hourlyprice
   , TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low') OR (recommendationoptions_1_migrationeffort = 'Medium')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low') OR (recommendationoptions_2_migrationeffort = 'Medium')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low') OR (recommendationoptions_3_migrationeffort = 'Medium')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(recommendationoptions_2_performancerisk, 'na'), ';', COALESCE(recommendationoptions_2_instancetype, 'na'), ';', COALESCE(recommendationoptions_2_migrationeffort, 'na'), ';', COALESCE(recommendationoptions_2_memory, 'na'), ';', COALESCE(recommendationoptions_2_vcpus, 'na'), ';', COALESCE(recommendationoptions_2_network, 'na'), ';', COALESCE(recommendationoptions_2_storage, 'na'), ';', CONCAT((CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_isarchitecturedifferent, 'na') = 'true') THEN 'Architecture ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_ishypervisordifferent, 'na') = 'true') THEN 'Hypervisor ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_isinstancestoreavailabilitydifferent, 'na') = 'true') THEN 'InstanceStoreAvailability ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_isnetworkinterfacedifferent, 'na') = 'true') THEN 'NetworkInterface ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_isstorageinterfacedifferent, 'na') = 'true') THEN 'StorageInterface ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_isvirtualizationtypedifferent, 'na') = 'true') THEN 'VirtualizationType ' ELSE '' END)), ';', COALESCE(recommendationoptions_2_projectedutilizationmetrics_cpu_maximum, 'na'), ';', COALESCE(recommendationoptions_2_projectedutilizationmetrics_memory_maximum, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE ((resourcearn LIKE '%arn:%') AND (recommendationoptions_2_estimatedmonthlysavings_currency <> ''))
UNION    SELECT
     TRY("date_parse"(lastrefreshtimestamp, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp
   , accountid accountid
   , resourcearn arn
   , TRY("split_part"(resourcearn, ':', 4)) region
   , TRY("split_part"(resourcearn, ':', 3)) service
   , TRY("split_part"(resourcearn, ':', 7)) name
   , 'rds' module
   , 'rds' recommendationsourcetype
   , instancefinding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , '' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , '' ressouce_details
   , '' utilizationmetrics
   , 'Option 3' option_name
   , currentdbinstanceclass option_from
   , recommendationoptions_3_instancetype option_to
   , recommendationoptions_3_estimatedmonthlysavings_currency currency
   , TRY((CAST(recommendationoptions_3_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(recommendationoptions_3_ondemandprice AS double)) hourlyprice
   , TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (((recommendationoptions_1_migrationeffort = '') OR (recommendationoptions_1_migrationeffort = 'VeryLow') OR (recommendationoptions_1_migrationeffort = 'Low') OR (recommendationoptions_1_migrationeffort = 'Medium')) AND (instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency <> '')) THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_2_migrationeffort = '') OR (recommendationoptions_2_migrationeffort = 'VeryLow') OR (recommendationoptions_2_migrationeffort = 'Low') OR (recommendationoptions_2_migrationeffort = 'Medium')) AND (recommendationoptions_2_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (((recommendationoptions_3_migrationeffort = '') OR (recommendationoptions_3_migrationeffort = 'VeryLow') OR (recommendationoptions_3_migrationeffort = 'Low') OR (recommendationoptions_3_migrationeffort = 'Medium')) AND (recommendationoptions_3_estimatedmonthlysavings_currency <> '')) THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(recommendationoptions_3_performancerisk, 'na'), ';', COALESCE(recommendationoptions_3_instancetype, 'na'), ';', COALESCE(recommendationoptions_3_migrationeffort, 'na'), ';', COALESCE(recommendationoptions_3_memory, 'na'), ';', COALESCE(recommendationoptions_3_vcpus, 'na'), ';', COALESCE(recommendationoptions_3_network, 'na'), ';', COALESCE(recommendationoptions_3_storage, 'na'), ';', CONCAT((CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_isarchitecturedifferent, 'na') = 'true') THEN 'Architecture ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_ishypervisordifferent, 'na') = 'true') THEN 'Hypervisor ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_isinstancestoreavailabilitydifferent, 'na') = 'true') THEN 'InstanceStoreAvailability ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_isnetworkinterfacedifferent, 'na') = 'true') THEN 'NetworkInterface ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_isstorageinterfacedifferent, 'na') = 'true') THEN 'StorageInterface ' ELSE '' END), (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_isvirtualizationtypedifferent, 'na') = 'true') THEN 'VirtualizationType ' ELSE '' END)), ';', COALESCE(recommendationoptions_3_projectedutilizationmetrics_cpu_maximum, 'na'), ';', COALESCE(recommendationoptions_3_projectedutilizationmetrics_memory_maximum, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_ec2_instance_lines
   WHERE ((resourcearn LIKE '%arn:%') AND (recommendationoptions_3_estimatedmonthlysavings_currency <> ''))
) 