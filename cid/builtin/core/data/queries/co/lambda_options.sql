CREATE OR REPLACE VIEW compute_optimizer_lambda_options AS
(
   SELECT
     TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
   , accountid accountid
   , functionarn arn
   , TRY("split_part"(functionarn, ':', 4)) region
   , TRY("split_part"(functionarn, ':', 3)) service
   , TRY("split_part"(functionarn, ':', 7)) name
   , 'lambda' module
   , 'lambda' recommendationsourcetype
   , finding finding
   , CONCAT(
        (CASE WHEN (findingreasoncodes_ismemoryoverprovisioned =  'true') THEN 'Memory-Over '      ELSE '' END),
        (CASE WHEN (findingreasoncodes_ismemoryunderprovisioned = 'true') THEN 'Memory-Under '     ELSE '' END),
        (CASE WHEN (findingreasoncodes_isinsufficientdata =       'true') THEN 'InsufficientData ' ELSE '' END),
        (CASE WHEN (findingreasoncodes_isinconclusive =           'true') THEN 'Inconclusive '     ELSE '' END)
    ) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk as currentperformancerisk
   , cast(NULL as varchar) errorcode
   , cast(NULL as varchar) errormessage
   , CONCAT(
         numberofinvocations , ';',
         current_costtotal , ';',
         currentconfiguration_timeout, ';',
         functionversion, ';') ressouce_details
   , CONCAT(
         utilizationmetrics_durationaverage, ';',
         utilizationmetrics_durationmaximum, ';',
         utilizationmetrics_memoryaverage, ';',
         utilizationmetrics_memorymaximum, ';'
    ) utilizationmetrics
   , 'Current' option_name
    , cast(NULL as varchar) option_from
   , cast(NULL as varchar) option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , try_cast(NULL as double) as monthlyprice
   , try_cast(NULL as double) as hourlyprice
   , 0E0 estimatedmonthlysavings_value
   , 0E0 estimatedmonthly_ondemand_cost_change
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_low
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium

   , CONCAT(
         currentperformancerisk, ';', -- '-'
         currentconfiguration_memorysize, ';',
         current_costaverage, ';',
         current_costaverage, ';',
         utilizationmetrics_durationaverage, ';',
         '', ';',
         utilizationmetrics_durationmaximum, ';'

       ) option_details
   FROM
     compute_optimizer_lambda_lines
   WHERE (functionarn LIKE '%arn:%')
UNION SELECT
     TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
   , accountid accountid
   , functionarn arn
   , TRY("split_part"(functionarn, ':', 4)) region
   , TRY("split_part"(functionarn, ':', 3)) service
   , TRY("split_part"(functionarn, ':', 7)) name
   , 'lambda' module
   , 'lambda' recommendationsourcetype
   , finding finding
   , cast(NULL as varchar) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk as currentperformancerisk
   , cast(NULL as varchar) errorcode
   , cast(NULL as varchar) errormessage
   , cast(NULL as varchar) ressouce_details
   , cast(NULL as varchar) utilizationmetrics
   , 'Option 1' as option_name
   , cast(NULL as varchar) option_from
   , cast(NULL as varchar) option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , cast(NULL as double) monthlyprice
   , cast(NULL as double) hourlyprice
   , try_cast(recommendationoptions_1_estimatedmonthlysavings_value as double) as estimatedmonthlysavings_value
   , try_cast(recommendationoptions_1_estimatedmonthlysavings_value as double) as estimatedmonthly_ondemand_cost_change
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_low
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium
   , CONCAT(
         '', ';',  --no performance risk
         recommendationoptions_1_configuration_memorysize, ';',
         recommendationoptions_1_costlow, ';',
         recommendationoptions_1_costhigh, ';',
         recommendationoptions_1_projectedutilizationmetrics_durationexpected,
         recommendationoptions_1_projectedutilizationmetrics_durationlowerbound, ';',
         recommendationoptions_1_projectedutilizationmetrics_durationupperbound, ';'
    ) option_details


    FROM
        compute_optimizer_lambda_lines
    WHERE
        functionarn LIKE '%arn:%'

UNION SELECT
     TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
   , accountid accountid
   , functionarn arn
   , TRY("split_part"(functionarn, ':', 4)) region
   , TRY("split_part"(functionarn, ':', 3)) service
   , TRY("split_part"(functionarn, ':', 7)) name
   , 'lambda' module
   , 'lambda' recommendationsourcetype
   , finding finding
   , cast(NULL as varchar) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk as currentperformancerisk
   , cast(NULL as varchar) errorcode
   , cast(NULL as varchar) errormessage
   , cast(NULL as varchar) ressouce_details
   , cast(NULL as varchar) utilizationmetrics
   , 'Option 2' as option_name
   , cast(NULL as varchar) option_from
   , cast(NULL as varchar) option_to
   , recommendationoptions_2_estimatedmonthlysavings_currency currency
   , cast(NULL as double) monthlyprice
   , cast(NULL as double) hourlyprice
   , try_cast(recommendationoptions_2_estimatedmonthlysavings_value as double) as estimatedmonthlysavings_value
   , try_cast(recommendationoptions_2_estimatedmonthlysavings_value as double) as estimatedmonthly_ondemand_cost_change
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_low
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium
   , CONCAT(
         '', ';',  --no performance risk
         recommendationoptions_2_configuration_memorysize, ';',
         recommendationoptions_2_costlow, ';',
         recommendationoptions_2_costhigh, ';',
         recommendationoptions_2_projectedutilizationmetrics_durationexpected,
         recommendationoptions_2_projectedutilizationmetrics_durationlowerbound, ';',
         recommendationoptions_2_projectedutilizationmetrics_durationupperbound, ';'
    ) option_details


    FROM
        compute_optimizer_lambda_lines
    WHERE
        functionarn LIKE '%arn:%'
       AND recommendationoptions_2_estimatedmonthlysavings_currency <> ''


UNION SELECT
     TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
   , accountid accountid
   , functionarn arn
   , TRY("split_part"(functionarn, ':', 4)) region
   , TRY("split_part"(functionarn, ':', 3)) service
   , TRY("split_part"(functionarn, ':', 7)) name
   , 'lambda' module
   , 'lambda' recommendationsourcetype
   , finding finding
   , cast(NULL as varchar) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk as currentperformancerisk
   , cast(NULL as varchar) errorcode
   , cast(NULL as varchar) errormessage
   , cast(NULL as varchar) ressouce_details
   , cast(NULL as varchar) utilizationmetrics
   , 'Option 3' as option_name
   , cast(NULL as varchar) option_from
   , cast(NULL as varchar) option_to
   , recommendationoptions_3_estimatedmonthlysavings_currency currency
   , cast(NULL as double) monthlyprice
   , cast(NULL as double) hourlyprice
   , try_cast(recommendationoptions_3_estimatedmonthlysavings_value as double) as estimatedmonthlysavings_value
   , try_cast(recommendationoptions_3_estimatedmonthlysavings_value as double) as estimatedmonthly_ondemand_cost_change
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_low
   , GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_currency != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium
   , CONCAT(
         '', ';',  --no performance risk
         recommendationoptions_3_configuration_memorysize, ';',
         recommendationoptions_3_costlow, ';',
         recommendationoptions_3_costhigh, ';',
         recommendationoptions_3_projectedutilizationmetrics_durationexpected,
         recommendationoptions_3_projectedutilizationmetrics_durationlowerbound, ';',
         recommendationoptions_3_projectedutilizationmetrics_durationupperbound, ';'
    ) option_details


    FROM
        compute_optimizer_lambda_lines
    WHERE
        functionarn LIKE '%arn:%'
       AND recommendationoptions_3_estimatedmonthlysavings_currency <> ''

)