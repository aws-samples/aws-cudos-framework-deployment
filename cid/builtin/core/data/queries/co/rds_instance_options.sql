CREATE OR REPLACE VIEW "compute_optimizer_rds_instance_options" AS
(
   SELECT
     TRY("date_parse"(lastrefreshtimestamp, '%Y-%m-%dT%H:%i:%s.%fZ')) lastrefreshtimestamp_utc
   , accountid accountid
   , resourcearn arn
   , TRY("split_part"(resourcearn, ':', 4)) region
   , TRY("split_part"(resourcearn, ':', 3)) service
   , TRY("split_part"(resourcearn, ':', 7)) name
   , 'rds_instance' module
   , 'rds_instance' recommendationsourcetype
   , instancefinding finding
   , CONCAT((CASE WHEN (instancefindingreasoncodes_iscpuoverprovisioned = 'true') THEN 'CPU-Over ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_iscpuunderprovisioned = 'true') THEN 'CPU-Under ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isebsiopsoverprovisioned = 'true') THEN 'EBSIOPS-Over ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isebsthroughputoverprovisioned = 'true') THEN 'EBSThroughput-Over ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isebsthroughputunderprovisioned = 'true') THEN 'EBSThroughput-Under ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isnetworkbandwidthoverprovisioned = 'true') THEN 'NetworkBandwidth-Over ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isnetworkbandwidthunderprovisioned = 'true') THEN 'NetworkBandwidth-Under ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isnewgenerationdbinstanceclassavailable = 'true') THEN 'NewGenDBInstanceClass-Available ' ELSE '' END), (CASE WHEN (instancefindingreasoncodes_isnewengineversionavailable = 'true') THEN 'NewEngineVersion-Available ' ELSE '' END)) reason
   , lookbackperiodindays lookbackperiodindays
   , 'none' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , effectiverecommendationpreferencesenhancedinfrastructuremetrics ressouce_details
   , CONCAT(utilizationmetricscpumaximum, ';', utilizationmetricsmemorymaximum, ';', utilizationmetricsnetworkreceivethroughputmaximum, ';', utilizationmetricsnetworktransmitthroughputmaximum, ';', utilizationmetricsebsvolumereadiopsmaximum, ';', utilizationmetricsebsvolumewriteiopsmaximum, ';', utilizationmetricsebsvolumereadthroughputmaximum, ';', utilizationmetricsebsvolumewritethroughputmaximum, ';', utilizationmetricsdatabaseconnectionsmaximum, ';') utilizationmetrics
   , 'Current' option_name
   , currentdbinstanceclass option_from
   , '' option_to
   , instanceRecommendationOptions_1_estimatedMonthlySavingsCurrency currency
   , TRY((CAST(currentinstanceondemandhourlyprice AS double) * 730)) monthlyprice
   , TRY(CAST(currentinstanceondemandhourlyprice AS double)) hourlyprice
   , 0E0 estimatedmonthlysavings_value
   , 0E0 estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(';', COALESCE(currentdbinstanceclass, 'na'), ';', ';', ';', ';', ';', ';', ';', COALESCE(currentinstanceondemandhourlyprice, 'na'), ';', ';', COALESCE(utilizationmetricscpumaximum, 'na'), ';') option_details
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
   , 'rds_instance' module
   , 'rds_instance' recommendationsourcetype
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
   , TRY((CAST(instancerecommendationoptions_1_instanceondemandhourlyprice AS double) * 730)) monthlyprice
   , TRY(CAST(instancerecommendationoptions_1_instanceondemandhourlyprice AS double)) hourlyprice
   , TRY(CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double)) estimatedmonthlysavings_value
   , TRY(((CAST(currentinstanceondemandhourlyprice AS double) * 730) - (CAST(instancerecommendationoptions_1_instanceondemandhourlyprice AS double) * 730))) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(instancerecommendationoptions_1_rank, 'na'), ';', COALESCE(instancerecommendationoptions_1_dbinstanceclass, 'na'), ';', COALESCE(instancerecommendationoptions_1_estimatedmonthlysavingscurrency, 'na'), ';', COALESCE(instancerecommendationoptions_1_estimatedmonthlysavingscurrencyafterdiscounts, 'na'), ';', COALESCE(instancerecommendationoptions_1_estimatedmonthlysavingscurrency, 'na'), ';', COALESCE(instancerecommendationoptions_1_estimatedmonthlysavingsvalue, 'na'), ';', COALESCE(instancerecommendationoptions_1_savingsopportunitypercentage, 'na'), ';', COALESCE(instancerecommendationoptions_1_savingsopportunityafterdiscountspercentage, 'na'), ';', COALESCE(instancerecommendationoptions_1_instanceondemandhourlyprice, 'na'), ';', COALESCE(instancerecommendationoptions_1_performancerisk, 'na'), ';', COALESCE(instancerecommendationoptions_1_projectedutilizationmetricscpumaximum, 'na'), ';') option_details
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
   , 'rds_instance' module
   , 'rds_instance' recommendationsourcetype
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
   , TRY((CAST(instancerecommendationoptions_2_instanceondemandhourlyprice AS double) * 730)) monthlyprice
   , TRY(CAST(instancerecommendationoptions_2_instanceondemandhourlyprice AS double)) hourlyprice
   , TRY(CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double)) estimatedmonthlysavings_value
   , TRY(((CAST(currentinstanceondemandhourlyprice AS double) * 730) - (CAST(instancerecommendationoptions_2_instanceondemandhourlyprice AS double) * 730))) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(instancerecommendationoptions_2_rank, 'na'), ';', COALESCE(instancerecommendationoptions_2_dbinstanceclass, 'na'), ';', COALESCE(instancerecommendationoptions_2_estimatedmonthlysavingscurrency, 'na'), ';', COALESCE(instancerecommendationoptions_2_estimatedmonthlysavingscurrencyafterdiscounts, 'na'), ';', COALESCE(instancerecommendationoptions_2_estimatedmonthlysavingscurrency, 'na'), ';', COALESCE(instancerecommendationoptions_2_estimatedmonthlysavingsvalue, 'na'), ';', COALESCE(instancerecommendationoptions_2_savingsopportunitypercentage, 'na'), ';', COALESCE(instancerecommendationoptions_2_savingsopportunityafterdiscountspercentage, 'na'), ';', COALESCE(instancerecommendationoptions_2_instanceondemandhourlyprice, 'na'), ';', COALESCE(instancerecommendationoptions_2_performancerisk, 'na'), ';', COALESCE(instancerecommendationoptions_2_projectedutilizationmetricscpumaximum, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE ((resourcearn LIKE '%arn:%') AND (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> ''))
UNION    SELECT
     TRY("date_parse"(lastrefreshtimestamp, '%Y-%m-%dT%H:%i:%s.%fZ')) lastrefreshtimestamp_utc
   , accountid accountid
   , resourcearn arn
   , TRY("split_part"(resourcearn, ':', 4)) region
   , TRY("split_part"(resourcearn, ':', 3)) service
   , TRY("split_part"(resourcearn, ':', 7)) name
   , 'rds_instance' module
   , 'rds_instance' recommendationsourcetype
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
   , TRY((CAST(instancerecommendationoptions_3_instanceondemandhourlyprice AS double) * 730)) monthlyprice
   , TRY(CAST(instancerecommendationoptions_3_instanceondemandhourlyprice AS double)) hourlyprice
   , TRY(CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double)) estimatedmonthlysavings_value
   , TRY(((CAST(currentinstanceondemandhourlyprice AS double) * 730) - (CAST(instancerecommendationoptions_3_instanceondemandhourlyprice AS double) * 730))) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (instancerecommendationoptions_1_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_1_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_2_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_2_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END), (CASE WHEN (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> '') THEN TRY_CAST(instancerecommendationoptions_3_estimatedmonthlysavingsvalue AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(instancerecommendationoptions_3_rank, 'na'), ';', COALESCE(instancerecommendationoptions_3_dbinstanceclass, 'na'), ';', COALESCE(instancerecommendationoptions_3_estimatedmonthlysavingscurrency, 'na'), ';', COALESCE(instancerecommendationoptions_3_estimatedmonthlysavingscurrencyafterdiscounts, 'na'), ';', COALESCE(instancerecommendationoptions_3_estimatedmonthlysavingscurrency, 'na'), ';', COALESCE(instancerecommendationoptions_3_estimatedmonthlysavingsvalue, 'na'), ';', COALESCE(instancerecommendationoptions_3_savingsopportunitypercentage, 'na'), ';', COALESCE(instancerecommendationoptions_3_savingsopportunityafterdiscountspercentage, 'na'), ';', COALESCE(instancerecommendationoptions_3_instanceondemandhourlyprice, 'na'), ';', COALESCE(instancerecommendationoptions_3_performancerisk, 'na'), ';', COALESCE(instancerecommendationoptions_3_projectedutilizationmetricscpumaximum, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_rds_instance_lines
   WHERE ((resourcearn LIKE '%arn:%') AND (instancerecommendationoptions_3_estimatedmonthlysavingscurrency <> ''))
)