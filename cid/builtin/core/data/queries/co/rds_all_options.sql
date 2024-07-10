CREATE OR REPLACE VIEW "compute_optimizer_rds_all_options" AS 
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
   , 'none' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , effectiverecommendationpreferencesenhancedinfrastructuremetrics ressouce_details
   , CONCAT(utilizationmetricscpumaximum, ';', utilizationmetricsmemorymaximum, ';', utilizationmetricsebsvolumestoragespaceutilizationmaximum, ';', utilizationmetricsnetworkreceivethroughputmaximum, ';', utilizationmetricsnetworktransmitthroughputmaximum, ';', utilizationmetricsebsvolumereadiopsmaximum, ';', utilizationmetricsebsvolumewriteiopsmaximum, ';', utilizationmetricsebsvolumereadthroughputmaximum, ';', utilizationmetricsebsvolumewritethroughputmaximum, ';', utilizationmetricsdatabaseconnectionsmaximum, ';') utilizationmetrics
   , 'Current' option_name
   , currentdbinstanceclass option_from
   , '' option_to
   , instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency currency
   , TRY((CAST(currentinstanceondemandhourlyprice AS double) * 730) + CAST(currentstorageondemandmonthlyprice AS double)) monthlyprice
   , TRY(CAST(currentinstanceondemandhourlyprice AS double) + (CAST(currentstorageondemandmonthlyprice AS double) / 730)) hourlyprice
   , TRY(CAST(currentinstanceondemandhourlyprice AS double)) rdscurrentinstanceondemandhourlyprice
   , TRY(CAST(currentstorageondemandmonthlyprice AS double) / 730) rdscurrentstorageondemandhourlyprice
   , 0E0 estimatedmonthlysavings_value
   , 0E0 estimatedmonthly_ondemand_cost_change
   , 0E0 max_estimatedmonthlysavings_value_very_low
   , 0E0 max_estimatedmonthlysavings_value_low
   , 0E0 max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(currentdbinstanceclass, 'na'), ';', ';', COALESCE(currentstorageconfigurationstoragetype, 'na'), ';', COALESCE(currentstorageconfigurationmaxallocatedstorage, 'na'), ';', COALESCE(currentstorageconfigurationallocatedstorage, 'na'), ';', COALESCE(currentstorageconfigurationiops, 'na'), ';', COALESCE(currentstorageconfigurationstoragethroughput, 'na'), ';') option_details
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
   , instancerecommendationoptions_1_dbinstanceclass option_to
   , instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency currency
   , TRY((CAST(instancerecommendationoptions_1_instanceondemandhourlyprice AS double) * 730) + CAST(storagerecommendationoptions_1_ondemandmonthlyprice AS double)) monthlyprice
   , TRY(CAST(instancerecommendationoptions_1_instanceondemandhourlyprice AS double) + (CAST(storagerecommendationoptions_1_ondemandmonthlyprice AS double) / 730)) hourlyprice
   , TRY(CAST(instancerecommendationoptions_1_instanceondemandhourlyprice AS double)) rdscurrentinstanceondemandhourlyprice
   , TRY(CAST(storagerecommendationoptions_1_ondemandmonthlyprice AS double) / 730) rdscurrentstorageondemandhourlyprice
   , TRY(CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) + CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue as double)) estimatedmonthlysavings_value
   , TRY(((CAST(currentinstanceondemandhourlyprice AS double) * 730) + CAST(currentstorageondemandmonthlyprice AS double)) - ((CAST(instancerecommendationoptions_1_instanceondemandhourlyprice AS double) * 730) + CAST(storagerecommendationoptions_1_ondemandmonthlyprice AS double))) estimatedmonthly_ondemand_cost_change
   , 0E0 max_estimatedmonthlysavings_value_very_low
   , 0E0 max_estimatedmonthlysavings_value_low
   , 0E0 max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(instancerecommendationoptions_1_performancerisk, 'na'), ';', COALESCE(instancerecommendationoptions_1_dbinstanceclass, 'na'), ';', COALESCE(instancerecommendationoptions_1_rank, 'na'), ';', COALESCE(instancerecommendationoptions_1_projectedutilizationmetricscpumaximum, 'na'), ';', COALESCE(storagerecommendationoptions_1_storagetype, 'na'), ';', COALESCE(storagerecommendationoptions_1_allocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_1_maxallocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_1_iops, 'na'), ';', COALESCE(storagerecommendationoptions_1_storagethroughput, 'na'), ';', COALESCE(storagerecommendationoptions_1_rank, 'na'), ';', COALESCE(storagerecommendationoptions_1_maxallocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_1_iops, 'na'), ';') option_details
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
   , instancerecommendationoptions_2_dbinstanceclass option_to
   , instanceRecommendationOptions_2_estimatedMonthlySavingsCurrency currency
   , TRY((CAST(instancerecommendationoptions_2_instanceondemandhourlyprice AS double) * 730) + CAST(storagerecommendationoptions_2_ondemandmonthlyprice AS double)) monthlyprice
   , TRY(CAST(instancerecommendationoptions_2_instanceondemandhourlyprice AS double) + (CAST(storagerecommendationoptions_2_ondemandmonthlyprice AS double) / 730)) hourlyprice
   , TRY(CAST(instancerecommendationoptions_2_instanceondemandhourlyprice AS double)) rdscurrentinstanceondemandhourlyprice
   , TRY(CAST(storagerecommendationoptions_2_ondemandmonthlyprice AS double) / 730) rdscurrentstorageondemandhourlyprice
   , TRY(CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) + CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue as double)) estimatedmonthlysavings_value
   , TRY(((CAST(currentinstanceondemandhourlyprice AS double) * 730) + CAST(currentstorageondemandmonthlyprice AS double)) - ((CAST(instancerecommendationoptions_2_instanceondemandhourlyprice AS double) * 730) + CAST(storagerecommendationoptions_2_ondemandmonthlyprice AS double))) estimatedmonthly_ondemand_cost_change
   , 0E0 max_estimatedmonthlysavings_value_very_low
   , 0E0 max_estimatedmonthlysavings_value_low
   , 0E0 max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(instancerecommendationoptions_2_performancerisk, 'na'), ';', COALESCE(instancerecommendationoptions_2_dbinstanceclass, 'na'), ';', COALESCE(instancerecommendationoptions_2_rank, 'na'), ';', COALESCE(instancerecommendationoptions_2_projectedutilizationmetricscpumaximum, 'na'), ';', COALESCE(storagerecommendationoptions_2_storagetype, 'na'), ';', COALESCE(storagerecommendationoptions_2_allocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_2_maxallocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_2_iops, 'na'), ';', COALESCE(storagerecommendationoptions_2_storagethroughput, 'na'), ';', COALESCE(storagerecommendationoptions_2_rank, 'na'), ';', COALESCE(storagerecommendationoptions_2_maxallocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_2_iops, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE ((resourcearn LIKE '%arn:%') AND (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> ''))
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
   , instancerecommendationoptions_3_dbinstanceclass option_to
   , instanceRecommendationOptions_3_estimatedMonthlySavingsCurrency currency
   , TRY((CAST(instancerecommendationoptions_3_instanceondemandhourlyprice AS double) * 730) + CAST(storagerecommendationoptions_3_ondemandmonthlyprice AS double)) monthlyprice
   , TRY(CAST(instancerecommendationoptions_3_instanceondemandhourlyprice AS double) + (CAST(storagerecommendationoptions_3_ondemandmonthlyprice AS double) / 730)) hourlyprice
   , TRY(CAST(instancerecommendationoptions_3_instanceondemandhourlyprice AS double)) rdscurrentinstanceondemandhourlyprice
   , TRY(CAST(storagerecommendationoptions_3_ondemandmonthlyprice AS double) / 730) rdscurrentstorageondemandhourlyprice
   , TRY(CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) + CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue as double)) estimatedmonthlysavings_value
   , TRY(((CAST(currentinstanceondemandhourlyprice AS double) * 730) + CAST(currentstorageondemandmonthlyprice AS double)) - ((CAST(instancerecommendationoptions_3_instanceondemandhourlyprice AS double) * 730) + CAST(storagerecommendationoptions_3_ondemandmonthlyprice AS double))) estimatedmonthly_ondemand_cost_change
   , 0E0 max_estimatedmonthlysavings_value_very_low
   , 0E0 max_estimatedmonthlysavings_value_low
   , 0E0 max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(instancerecommendationoptions_3_performancerisk, 'na'), ';', COALESCE(instancerecommendationoptions_3_dbinstanceclass, 'na'), ';', COALESCE(instancerecommendationoptions_3_rank, 'na'), ';', COALESCE(instancerecommendationoptions_3_projectedutilizationmetricscpumaximum, 'na'), ';', COALESCE(storagerecommendationoptions_3_storagetype, 'na'), ';', COALESCE(storagerecommendationoptions_3_allocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_3_maxallocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_3_iops, 'na'), ';', COALESCE(storagerecommendationoptions_3_storagethroughput, 'na'), ';', COALESCE(storagerecommendationoptions_3_rank, 'na'), ';', COALESCE(storagerecommendationoptions_3_maxallocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_3_iops, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE ((resourcearn LIKE '%arn:%') AND (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> ''))
) 