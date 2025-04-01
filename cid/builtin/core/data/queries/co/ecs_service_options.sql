CREATE OR REPLACE VIEW compute_optimizer_ecs_service_options AS
(
   SELECT
     TRY("date_parse"(lastrefreshtimestamp_utc, '%Y-%m-%dT%H:%i:%s.%fZ')) lastrefreshtimestamp_utc
   , accountid accountid
   , servicearn arn
   , TRY("split_part"(servicearn, ':', 4)) region
   , TRY("split_part"(servicearn, ':', 3)) service
   , TRY("split_part"(servicearn, '/', 3)) name
   , 'ecs_service' module
   , effectiverecommendationpreferencessavingsestimationmodesource recommendationsourcetype
   , finding finding
   , CONCAT(
        (CASE WHEN (findingreasoncodes_iscpuoverprovisioned =               'TRUE') THEN 'CPU-Over '               ELSE '' END),
        (CASE WHEN (findingreasoncodes_iscpuunderprovisioned =              'TRUE') THEN 'CPU-Under '              ELSE '' END),
        (CASE WHEN (findingreasoncodes_ismemoryoverprovisioned =            'TRUE') THEN 'Memory-Over '            ELSE '' END),
        (CASE WHEN (findingreasoncodes_ismemoryunderprovisioned =           'TRUE') THEN 'Memory-Under '           ELSE '' END)
    ) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk as currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , '' ressouce_details
   , CONCAT(
        utilizationmetrics_cpu_maximum, ';',
        CAST(TRY(CAST(utilizationmetrics_cpu_maximum AS double)/CAST(currentserviceconfiguration_cpu AS double)) as varchar), ';',
        CAST(TRY(CAST(utilizationmetrics_cpu_maximum AS double)/CAST(recommendationoptions_1_cpu AS double)) as varchar), ';',
        utilizationmetrics_memory_maximum, ';',
        CAST(TRY((CAST(utilizationmetrics_memory_maximum AS double))/TRY(CAST(currentserviceconfiguration_memory AS double))) as varchar), ';',
        CAST(TRY((CAST(utilizationmetrics_memory_maximum AS double))/TRY(CAST(recommendationoptions_1_memory AS double))) as varchar), ';',
        '', ';',
        '', ';',
        '', ';',
        ''
        ) utilizationmetrics
   , 'Current' option_name
   , CONCAT(
        currentserviceconfiguration_cpu, ';',
        currentserviceconfiguration_memory
        ) option_from
   , '' option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , 0E0 monthlyprice
   , 0E0 hourlyprice
   , 0E0 estimatedmonthlysavings_value
   , 0E0 estimatedmonthly_ondemand_cost_change
   , COALESCE(TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double), 0E0) as max_estimatedmonthlysavings_value_very_low
   , COALESCE(TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double), 0E0) as max_estimatedmonthlysavings_value_low
   , COALESCE(TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double), 0E0) as max_estimatedmonthlysavings_value_medium
   , CONCAT(
        CONCAT(TRY("split_part"(servicearn, '/', 2)), ';'),
        CONCAT(COALESCE(recommendations_count, ''), ';'),        
        '', ';',
        '', ';',
        '', ';',
        CONCAT(COALESCE(TRY("split_part"(currentserviceconfiguration_taskdefinitionarn, '/', 2)), ''), ';'),        
        CONCAT(COALESCE(currentserviceconfiguration_taskdefinitionarn, ''), ';'),        
        CONCAT(COALESCE(currentperformancerisk, ''), ';'),
        CONCAT(COALESCE(currentserviceconfiguration_autoscalingconfiguration, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_1_containername, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_2_containername, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_3_containername, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_4_containername, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_5_containername, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_6_containername, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_7_containername, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_8_containername, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_9_containername, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_10_containername, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_1_memory, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_1_memoryreservation, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_2_memory, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_2_memoryreservation, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_3_memory, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_3_memoryreservation, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_4_memory, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_4_memoryreservation, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_5_memory, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_5_memoryreservation, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_6_memory, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_6_memoryreservation, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_7_memory, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_7_memoryreservation, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_8_memory, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_8_memoryreservation, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_9_memory, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_9_memoryreservation, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_10_memory, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_10_memoryreservation, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_1_cpu, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_2_cpu, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_3_cpu, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_4_cpu, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_5_cpu, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_6_cpu, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_7_cpu, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_8_cpu, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_9_cpu, ''), ';'),
        CONCAT(COALESCE(currentservicecontainerconfiguration_10_cpu, ''), ';'),
        CONCAT('', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';')
   ) option_details
   , tags tags
   FROM
     compute_optimizer_ecs_service_lines
   WHERE (servicearn LIKE '%arn:%')
UNION SELECT
     TRY("date_parse"(lastrefreshtimestamp_utc, '%Y-%m-%dT%H:%i:%s.%fZ')) lastrefreshtimestamp_utc
   , accountid accountid
   , servicearn arn
   , TRY("split_part"(servicearn, ':', 4)) region
   , TRY("split_part"(servicearn, ':', 3)) service
   , TRY("split_part"(servicearn, '/', 3)) name
   , 'ecs_service' module
   , effectiverecommendationpreferencessavingsestimationmodesource recommendationsourcetype
   , finding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , '' currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , 'na' ressouce_details
   , CONCAT(
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        recommendationoptions_1_projectedutilizationmetrics_cpu_maximum_upperboundvalue, ';',
        recommendationoptions_1_projectedutilizationmetrics_cpu_maximum_lowerboundvalue, ';',
        recommendationoptions_1_projectedutilizationmetrics_memory_maximum_upperboundvalue, ';',
        recommendationoptions_1_projectedutilizationmetrics_memory_maximum_lowerboundvalue
        ) utilizationmetrics
   , 'Recommendation' option_name
   , '' option_from
   , CONCAT(
        recommendationoptions_1_cpu, ';',
        recommendationoptions_1_memory
        ) option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , 0E0 monthlyprice
   , 0E0 hourlyprice
   , COALESCE(TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double), 0E0) as estimatedmonthlysavings_value
   , COALESCE(TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double), 0E0) as estimatedmonthly_ondemand_cost_change
   , COALESCE(TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double), 0E0) as max_estimatedmonthlysavings_value_very_low
   , COALESCE(TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double), 0E0) as max_estimatedmonthlysavings_value_low
   , COALESCE(TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double), 0E0) as max_estimatedmonthlysavings_value_medium
   , CONCAT(
        CONCAT(TRY("split_part"(servicearn, '/', 2)), ';'),
        CONCAT(COALESCE(recommendations_count, ''), ';'),
        CONCAT(
        COALESCE(recommendationoptions_1_savingsopportunitypercentage, ''), ';',
        COALESCE(recommendationoptions_1_estimatedmonthlysavingsafterdiscounts_value, ''), ';',
        COALESCE(recommendationoptions_1_savingsopportunitypercentageafterdiscounts, ''), ';',
        COALESCE(TRY("split_part"(currentserviceconfiguration_taskdefinitionarn, '/', 2)), ''), ';',
        COALESCE(currentserviceconfiguration_taskdefinitionarn, ''), ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';',
        '', ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemory_1, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemoryreservation_1, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemory_2, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemoryreservation_2, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemory_3, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemoryreservation_3, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemory_4, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemoryreservation_4, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemory_5, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemoryreservation_5, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemory_6, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemoryreservation_6, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemory_7, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemoryreservation_7, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemory_8, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemoryreservation_8, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemory_9, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemoryreservation_9, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemory_10, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containermemoryreservation_10, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containercpu_1, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containercpu_2, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containercpu_3, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containercpu_4, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containercpu_5, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containercpu_6, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containercpu_7, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containercpu_8, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containercpu_9, ''), ';'),
        CONCAT(COALESCE(recommendationoptions_1_containercpu_10, ''), ';')
   ) option_details
   , tags tags
   FROM
     compute_optimizer_ecs_service_lines
   WHERE (servicearn LIKE '%arn:%')
 )