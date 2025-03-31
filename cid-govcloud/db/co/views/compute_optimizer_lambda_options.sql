CREATE OR REPLACE VIEW compute_optimizer_lambda_options AS
(
   SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , functionarn arn
   , TRY("split_part"(functionarn, ':', 4)) region
   , TRY("split_part"(functionarn, ':', 3)) service
   , TRY("split_part"(functionarn, ':', 7)) name
   , 'lambda' module
   , 'lambda' recommendationsourcetype
   , finding finding
   , CONCAT((CASE WHEN (findingreasoncodes_ismemoryoverprovisioned = 'true') THEN 'Memory-Over ' ELSE '' END), (CASE WHEN (findingreasoncodes_ismemoryunderprovisioned = 'true') THEN 'Memory-Under ' ELSE '' END), (CASE WHEN (findingreasoncodes_isinsufficientdata = 'true') THEN 'InsufficientData ' ELSE '' END), (CASE WHEN (findingreasoncodes_isinconclusive = 'true') THEN 'Inconclusive ' ELSE '' END)) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , CAST(null AS varchar(1)) errorcode
   , CAST(null AS varchar(1)) errormessage
   , CONCAT(numberofinvocations, ';', current_costtotal, ';', currentconfiguration_timeout, ';', functionversion, ';') ressouce_details
   , CONCAT(utilizationmetrics_durationaverage, ';', utilizationmetrics_durationmaximum, ';', utilizationmetrics_memoryaverage, ';', utilizationmetrics_memorymaximum, ';') utilizationmetrics
   , 'Current' option_name
   , CAST(null AS varchar(1)) option_from
   , CAST(null AS varchar(1)) option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , TRY_CAST(null AS double) monthlyprice
   , TRY_CAST(null AS double) hourlyprice
   , 0E0 estimatedmonthlysavings_value
   , 0E0 estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(currentperformancerisk, 'na'), ';', COALESCE(currentconfiguration_memorysize, 'na'), ';', COALESCE(current_costaverage, 'na'), ';', COALESCE(current_costaverage, 'na'), ';', COALESCE(utilizationmetrics_durationaverage, 'na'), ';', '', ';', COALESCE(utilizationmetrics_durationmaximum, 'na'), ';') option_details
   , CAST('' AS varchar(1)) tags
   FROM
     compute_optimizer_lambda_lines
   WHERE (functionarn LIKE '%arn:%')
UNION    SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , functionarn arn
   , TRY("split_part"(functionarn, ':', 4)) region
   , TRY("split_part"(functionarn, ':', 3)) service
   , TRY("split_part"(functionarn, ':', 7)) name
   , 'lambda' module
   , 'lambda' recommendationsourcetype
   , finding finding
   , CAST(null AS varchar(1)) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , CAST(null AS varchar(1)) errorcode
   , CAST(null AS varchar(1)) errormessage
   , CAST(null AS varchar(1)) ressouce_details
   , CAST(null AS varchar(1)) utilizationmetrics
   , 'Option 1' option_name
   , CAST(null AS varchar(1)) option_from
   , CAST(null AS varchar(1)) option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , CAST(null AS double) monthlyprice
   , CAST(null AS double) hourlyprice
   , TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT('', ';', COALESCE(recommendationoptions_1_configuration_memorysize, 'na'), ';', COALESCE(recommendationoptions_1_costlow, 'na'), ';', COALESCE(recommendationoptions_1_costhigh, 'na'), ';', COALESCE(recommendationoptions_1_projectedutilizationmetrics_durationexpected, 'na'), ';', COALESCE(recommendationoptions_1_projectedutilizationmetrics_durationlowerbound, 'na'), ';', COALESCE(recommendationoptions_1_projectedutilizationmetrics_durationupperbound, 'na'), ';') option_details
   , CAST('' AS varchar(1)) tags
   FROM
     compute_optimizer_lambda_lines
   WHERE (functionarn LIKE '%arn:%')
UNION    SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , functionarn arn
   , TRY("split_part"(functionarn, ':', 4)) region
   , TRY("split_part"(functionarn, ':', 3)) service
   , TRY("split_part"(functionarn, ':', 7)) name
   , 'lambda' module
   , 'lambda' recommendationsourcetype
   , finding finding
   , CAST(null AS varchar(1)) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , CAST(null AS varchar(1)) errorcode
   , CAST(null AS varchar(1)) errormessage
   , CAST(null AS varchar(1)) ressouce_details
   , CAST(null AS varchar(1)) utilizationmetrics
   , 'Option 2' option_name
   , CAST(null AS varchar(1)) option_from
   , CAST(null AS varchar(1)) option_to
   , recommendationoptions_2_estimatedmonthlysavings_currency currency
   , CAST(null AS double) monthlyprice
   , CAST(null AS double) hourlyprice
   , TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT('', ';', COALESCE(recommendationoptions_2_configuration_memorysize, 'na'), ';', COALESCE(recommendationoptions_2_costlow, 'na'), ';', COALESCE(recommendationoptions_2_costhigh, 'na'), ';', COALESCE(recommendationoptions_2_projectedutilizationmetrics_durationexpected, 'na'), ';', COALESCE(recommendationoptions_2_projectedutilizationmetrics_durationlowerbound, 'na'), ';', COALESCE(recommendationoptions_2_projectedutilizationmetrics_durationupperbound, 'na'), ';') option_details
   , CAST('' AS varchar(1)) tags
   FROM
     compute_optimizer_lambda_lines
   WHERE ((functionarn LIKE '%arn:%') AND (recommendationoptions_2_estimatedmonthlysavings_currency <> ''))
UNION    SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , functionarn arn
   , TRY("split_part"(functionarn, ':', 4)) region
   , TRY("split_part"(functionarn, ':', 3)) service
   , TRY("split_part"(functionarn, ':', 7)) name
   , 'lambda' module
   , 'lambda' recommendationsourcetype
   , finding finding
   , CAST(null AS varchar(1)) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , CAST(null AS varchar(1)) errorcode
   , CAST(null AS varchar(1)) errormessage
   , CAST(null AS varchar(1)) ressouce_details
   , CAST(null AS varchar(1)) utilizationmetrics
   , 'Option 3' option_name
   , CAST(null AS varchar(1)) option_from
   , CAST(null AS varchar(1)) option_to
   , recommendationoptions_3_estimatedmonthlysavings_currency currency
   , CAST(null AS double) monthlyprice
   , CAST(null AS double) hourlyprice
   , TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_currency <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT('', ';', COALESCE(recommendationoptions_3_configuration_memorysize, 'na'), ';', COALESCE(recommendationoptions_3_costlow, 'na'), ';', COALESCE(recommendationoptions_3_costhigh, 'na'), ';', COALESCE(recommendationoptions_3_projectedutilizationmetrics_durationexpected, 'na'), ';', COALESCE(recommendationoptions_3_projectedutilizationmetrics_durationlowerbound, 'na'), ';', COALESCE(recommendationoptions_3_projectedutilizationmetrics_durationupperbound, 'na'), ';') option_details
   , CAST(null AS varchar(1)) tags
   FROM
     compute_optimizer_lambda_lines
   WHERE ((functionarn LIKE '%arn:%') AND (recommendationoptions_3_estimatedmonthlysavings_currency <> ''))
) 
