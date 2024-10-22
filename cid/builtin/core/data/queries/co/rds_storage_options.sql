CREATE OR REPLACE VIEW "compute_optimizer_rds_storage_options" AS
(
   SELECT
     TRY("date_parse"(lastrefreshtimestamp, '%Y-%m-%dT%H:%i:%s.%fZ')) lastrefreshtimestamp_utc
   , accountid accountid
   , resourcearn arn
   , TRY("split_part"(resourcearn, ':', 4)) region
   , TRY("split_part"(resourcearn, ':', 3)) service
   , TRY("split_part"(resourcearn, ':', 7)) name
   , 'rds_storage' module
   , 'rds_storage' recommendationsourcetype
   , storagefinding finding
   , CONCAT((CASE WHEN (storagefindingreasoncodes_isebsvolumeallocatedstorageunderprovisioned = 'true') THEN 'AllocatedStorage-Under ' ELSE '' END), (CASE WHEN (storagefindingreasoncodes_isebsvolumethroughputunderprovisioned = 'true') THEN 'VolumeThroughput-Under ' ELSE '' END), (CASE WHEN (storagefindingreasoncodes_isebsvolumeiopsoverprovisioned = 'true') THEN 'VolumeIOPS-Over ' ELSE '' END), (CASE WHEN (storagefindingreasoncodes_isebsvolumethroughputoverprovisioned = 'true') THEN 'VolumeThroughput-Over ' ELSE '' END), (CASE WHEN (storagefindingreasoncodes_isnewgenerationstoragetypeavailable = 'true') THEN 'NewGenStorageType-Available ' ELSE '' END)) reason
   , lookbackperiodindays lookbackperiodindays
   , 'none' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , effectiverecommendationpreferencesenhancedinfrastructuremetrics ressouce_details
   , CONCAT(utilizationmetricsebsvolumereadiopsmaximum, ';', utilizationmetricsebsvolumewriteiopsmaximum, ';', utilizationmetricsebsvolumereadthroughputmaximum, ';', utilizationmetricsebsvolumewritethroughputmaximum, ';', utilizationmetricsebsvolumestoragespaceutilizationmaximum, ';') utilizationmetrics
   , 'Current' option_name
   , currentstorageconfigurationstoragetype option_from
   , '' option_to
   , storagerecommendationoptions_1_estimatedmonthlysavingscurrency currency
   , TRY(CAST(currentstorageondemandmonthlyprice AS double)) monthlyprice
   , TRY((CAST(currentstorageondemandmonthlyprice AS double) / 730)) hourlyprice
   , 0E0 estimatedmonthlysavings_value
   , 0E0 estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(';', COALESCE(currentstorageconfigurationstoragetype, 'na'), ';', ';', ';', ';', ';', ';', COALESCE(currentstorageconfigurationallocatedstorage, 'na'), ';', COALESCE(currentstorageconfigurationiops, 'na'), ';', COALESCE(currentstorageconfigurationstoragethroughput, 'na'), ';', COALESCE(currentstorageconfigurationmaxallocatedstorage, 'na'), ';', COALESCE(currentstorageondemandmonthlyprice, 'na'), ';', ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE (resourcearn LIKE '%arn:%')
UNION    SELECT
     TRY("date_parse"(lastrefreshtimestamp, '%Y-%m-%dT%H:%i:%s.%fZ')) lastrefreshtimestamp_utc
   , accountid accountid
   , resourcearn arn
   , TRY("split_part"(resourcearn, ':', 4)) region
   , TRY("split_part"(resourcearn, ':', 3)) service
   , TRY("split_part"(resourcearn, ':', 7)) name
   , 'rds_storage' module
   , 'rds_storage' recommendationsourcetype
   , storagefinding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , '' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , '' ressouce_details
   , '' utilizationmetrics
   , 'Option 1' option_name
   , currentstorageconfigurationstoragetype option_from
   , storagerecommendationoptions_1_storagetype option_to
   , storagerecommendationoptions_1_estimatedmonthlysavingscurrency currency
   , TRY(CAST(storagerecommendationoptions_1_ondemandmonthlyprice AS double)) monthlyprice
   , TRY((CAST(storagerecommendationoptions_1_ondemandmonthlyprice AS double) / 730)) hourlyprice
   , TRY(CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double)) estimatedmonthlysavings_value
   , TRY((CAST(currentstorageondemandmonthlyprice AS double) - CAST(storagerecommendationoptions_1_ondemandmonthlyprice AS double))) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(storagerecommendationoptions_1_rank, 'na'), ';', COALESCE(storagerecommendationoptions_1_storagetype, 'na'), ';', COALESCE(storagerecommendationoptions_1_estimatedmonthlysavingscurrencyafterdiscounts, 'na'), ';', COALESCE(storagerecommendationoptions_1_estimatedmonthlysavingsvalueafterdiscounts, 'na'), ';', COALESCE(storagerecommendationoptions_1_estimatedmonthlysavingscurrency, 'na'), ';', COALESCE(storagerecommendationoptions_1_estimatedmonthlysavingsvalue, 'na'), ';', COALESCE(storagerecommendationoptions_1_savingsopportunitypercentage, 'na'), ';', COALESCE(storagerecommendationoptions_1_allocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_1_iops, 'na'), ';', COALESCE(storagerecommendationoptions_1_storagethroughput, 'na'), ';', COALESCE(storagerecommendationoptions_1_maxallocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_1_ondemandmonthlyprice, 'na'), ';', COALESCE(storagerecommendationoptions_1_savingsopportunityafterdiscountspercentage, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE (resourcearn LIKE '%arn:%')
UNION    SELECT
     TRY("date_parse"(lastrefreshtimestamp, '%Y-%m-%dT%H:%i:%s.%fZ')) lastrefreshtimestamp_utc
   , accountid accountid
   , resourcearn arn
   , TRY("split_part"(resourcearn, ':', 4)) region
   , TRY("split_part"(resourcearn, ':', 3)) service
   , TRY("split_part"(resourcearn, ':', 7)) name
   , 'rds_storage' module
   , 'rds_storage' recommendationsourcetype
   , storagefinding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , '' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , '' ressouce_details
   , '' utilizationmetrics
   , 'Option 2' option_name
   , currentstorageconfigurationstoragetype option_from
   , storagerecommendationoptions_2_storagetype option_to
   , storagerecommendationoptions_2_estimatedmonthlysavingscurrency currency
   , TRY(CAST(storagerecommendationoptions_2_ondemandmonthlyprice AS double)) monthlyprice
   , TRY((CAST(storagerecommendationoptions_2_ondemandmonthlyprice AS double) / 730)) hourlyprice
   , TRY(CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double)) estimatedmonthlysavings_value
   , TRY((CAST(currentstorageondemandmonthlyprice AS double) - CAST(storagerecommendationoptions_2_ondemandmonthlyprice AS double))) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(storagerecommendationoptions_2_rank, 'na'), ';', COALESCE(storagerecommendationoptions_2_storagetype, 'na'), ';', COALESCE(storagerecommendationoptions_2_estimatedmonthlysavingscurrencyafterdiscounts, 'na'), ';', COALESCE(storagerecommendationoptions_2_estimatedmonthlysavingsvalueafterdiscounts, 'na'), ';', COALESCE(storagerecommendationoptions_2_estimatedmonthlysavingscurrency, 'na'), ';', COALESCE(storagerecommendationoptions_2_estimatedmonthlysavingsvalue, 'na'), ';', COALESCE(storagerecommendationoptions_2_savingsopportunitypercentage, 'na'), ';', COALESCE(storagerecommendationoptions_2_allocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_2_iops, 'na'), ';', COALESCE(storagerecommendationoptions_2_storagethroughput, 'na'), ';', COALESCE(storagerecommendationoptions_2_maxallocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_2_ondemandmonthlyprice, 'na'), ';', COALESCE(storagerecommendationoptions_2_savingsopportunityafterdiscountspercentage, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE ((resourcearn LIKE '%arn:%') AND (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> ''))
UNION    SELECT
     TRY("date_parse"(lastrefreshtimestamp, '%Y-%m-%dT%H:%i:%s.%fZ')) lastrefreshtimestamp_utc
   , accountid accountid
   , resourcearn arn
   , TRY("split_part"(resourcearn, ':', 4)) region
   , TRY("split_part"(resourcearn, ':', 3)) service
   , TRY("split_part"(resourcearn, ':', 7)) name
   , 'rds_storage' module
   , 'rds_storage' recommendationsourcetype
   , storagefinding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , '' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , '' ressouce_details
   , '' utilizationmetrics
   , 'Option 3' option_name
   , currentstorageconfigurationstoragetype option_from
   , storagerecommendationoptions_3_storagetype option_to
   , storagerecommendationoptions_3_estimatedmonthlysavingscurrency currency
   , TRY(CAST(storagerecommendationoptions_3_ondemandmonthlyprice AS double)) monthlyprice
   , TRY((CAST(storagerecommendationoptions_3_ondemandmonthlyprice AS double) / 730)) hourlyprice
   , TRY(CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double)) estimatedmonthlysavings_value
   , TRY((CAST(currentstorageondemandmonthlyprice AS double) - CAST(storagerecommendationoptions_3_ondemandmonthlyprice AS double))) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (storagerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(storagerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(storagerecommendationoptions_3_rank, 'na'), ';', COALESCE(storagerecommendationoptions_3_storagetype, 'na'), ';', COALESCE(storagerecommendationoptions_3_estimatedmonthlysavingscurrencyafterdiscounts, 'na'), ';', COALESCE(storagerecommendationoptions_3_estimatedmonthlysavingsvalueafterdiscounts, 'na'), ';', COALESCE(storagerecommendationoptions_3_estimatedmonthlysavingscurrency, 'na'), ';', COALESCE(storagerecommendationoptions_3_estimatedmonthlysavingsvalue, 'na'), ';', COALESCE(storagerecommendationoptions_3_savingsopportunitypercentage, 'na'), ';', COALESCE(storagerecommendationoptions_3_allocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_3_iops, 'na'), ';', COALESCE(storagerecommendationoptions_3_storagethroughput, 'na'), ';', COALESCE(storagerecommendationoptions_3_maxallocatedstorage, 'na'), ';', COALESCE(storagerecommendationoptions_3_ondemandmonthlyprice, 'na'), ';', COALESCE(storagerecommendationoptions_3_savingsopportunityafterdiscountspercentage, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE ((resourcearn LIKE '%arn:%') AND (storagerecommendationoptions_3_estimatedmonthlysavingscurrency <> ''))
)