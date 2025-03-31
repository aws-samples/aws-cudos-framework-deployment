CREATE OR REPLACE VIEW compute_optimizer_ebs_volume_options AS
(
   SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , volumearn arn
   , TRY(split_part(volumearn, ':', 4)) region
   , TRY(split_part(volumearn, ':', 3)) service
   , TRY(split_part(volumearn, ':', 7)) name
   , 'ebs_volume' module
   , 'ebs_volume' recommendationsourcetype
   , finding finding
   , CAST(null AS varchar(1)) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CAST(null AS varchar(1)) ressouce_details
   , CONCAT(utilizationmetrics_volumereadopspersecondmaximum, ';', utilizationmetrics_volumewriteopspersecondmaximum, ';', utilizationmetrics_volumereadbytespersecondmaximum, ';', utilizationmetrics_volumewritebytespersecondmaximum, ';') utilizationmetrics
   , 'Current' option_name
   , currentconfiguration_volumetype option_from
   , CAST(null AS varchar(1)) option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , TRY_CAST(current_monthlyprice AS double) monthlyprice
   , TRY((CAST(current_monthlyprice AS double) / 730)) hourlyprice
   , 0E0 estimatedmonthlysavings_value
   , 0E0 estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(currentperformancerisk, 'na'), ';', COALESCE(currentconfiguration_volumetype, 'na'), ';', COALESCE(currentconfiguration_volumesize, 'na'), ';', COALESCE(currentconfiguration_volumebaselineiops, 'na'), ';', COALESCE(currentconfiguration_volumebaselinethroughput, 'na'), ';', COALESCE(currentconfiguration_volumeburstiops, 'na'), ';', COALESCE(currentconfiguration_volumeburstthroughput, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_ebs_volume_lines
   WHERE (volumearn LIKE '%arn:%')
UNION    SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , volumearn arn
   , TRY(split_part(volumearn, ':', 4)) region
   , TRY(split_part(volumearn, ':', 3)) service
   , TRY(split_part(volumearn, ':', 7)) name
   , 'ebs_volume' module
   , 'ebs_volume' recommendationsourcetype
   , finding finding
   , CAST(null AS varchar(1)) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CAST(null AS varchar(1)) ressouce_details
   , CAST(null AS varchar(1)) utilizationmetrics
   , 'Option 1' option_name
   , currentconfiguration_volumetype option_from
   , recommendationoptions_1_configuration_volumetype option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , TRY_CAST(recommendationoptions_1_monthlyprice AS double) monthlyprice
   , TRY((CAST(recommendationoptions_1_monthlyprice AS double) / 730)) hourlyprice
   , TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(recommendationoptions_1_performancerisk, 'na'), ';', COALESCE(recommendationoptions_1_configuration_volumetype, 'na'), ';', COALESCE(recommendationoptions_1_configuration_volumesize, 'na'), ';', COALESCE(recommendationoptions_1_configuration_volumebaselineiops, 'na'), ';', COALESCE(recommendationoptions_1_configuration_volumebaselinethroughput, 'na'), ';', COALESCE(recommendationoptions_1_configuration_volumeburstiops, 'na'), ';', COALESCE(recommendationoptions_1_configuration_volumeburstthroughput, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_ebs_volume_lines
   WHERE ((volumearn LIKE '%arn:%') AND (recommendationoptions_1_configuration_volumetype <> ''))
UNION    SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , volumearn arn
   , TRY(split_part(volumearn, ':', 4)) region
   , TRY(split_part(volumearn, ':', 3)) service
   , TRY(split_part(volumearn, ':', 7)) name
   , 'ebs_volume' module
   , 'ebs_volume' recommendationsourcetype
   , finding finding
   , CAST(null AS varchar(1)) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CAST(null AS varchar(1)) ressouce_details
   , CAST(null AS varchar(1)) utilizationmetrics
   , 'Option 2' option_name
   , currentconfiguration_volumetype option_from
   , recommendationoptions_2_configuration_volumetype option_to
   , recommendationoptions_2_estimatedmonthlysavings_currency currency
   , TRY_CAST(recommendationoptions_2_monthlyprice AS double) monthlyprice
   , TRY((CAST(recommendationoptions_2_monthlyprice AS double) / 730)) hourlyprice
   , TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(recommendationoptions_2_performancerisk, 'na'), ';', COALESCE(recommendationoptions_2_configuration_volumetype, 'na'), ';', COALESCE(recommendationoptions_2_configuration_volumesize, 'na'), ';', COALESCE(recommendationoptions_2_configuration_volumebaselineiops, 'na'), ';', COALESCE(recommendationoptions_2_configuration_volumebaselinethroughput, 'na'), ';', COALESCE(recommendationoptions_2_configuration_volumeburstiops, 'na'), ';', COALESCE(recommendationoptions_2_configuration_volumeburstthroughput, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_ebs_volume_lines
   WHERE ((volumearn LIKE '%arn:%') AND (recommendationoptions_2_configuration_volumetype <> ''))
UNION    SELECT
     COALESCE(
        TRY(date_parse(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')),
        TRY(date_parse(lastrefreshtimestamp_utc, '%m/%d/%y %H:%i'))
    ) AS lastrefreshtimestamp_utc
   , accountid accountid
   , volumearn arn
   , TRY(split_part(volumearn, ':', 4)) region
   , TRY(split_part(volumearn, ':', 3)) service
   , TRY(split_part(volumearn, ':', 7)) name
   , 'ebs_volume' module
   , 'ebs_volume' recommendationsourcetype
   , finding finding
   , CAST(null AS varchar(1)) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CAST(null AS varchar(1)) ressouce_details
   , CAST(null AS varchar(1)) utilizationmetrics
   , 'Option 3' option_name
   , currentconfiguration_volumetype option_from
   , recommendationoptions_3_configuration_volumetype option_to
   , recommendationoptions_3_estimatedmonthlysavings_currency currency
   , TRY_CAST(recommendationoptions_3_monthlyprice AS double) monthlyprice
   , TRY((CAST(recommendationoptions_3_monthlyprice AS double) / 730)) hourlyprice
   , TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) estimatedmonthly_ondemand_cost_change
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_very_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_low
   , GREATEST((CASE WHEN (recommendationoptions_1_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_1_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_1_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_2_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_2_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_2_monthlyprice AS double))) ELSE 0E0 END), (CASE WHEN (recommendationoptions_3_estimatedmonthlysavings_value <> '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) WHEN (recommendationoptions_3_monthlyprice <> '') THEN TRY((CAST(current_monthlyprice AS double) - CAST(recommendationoptions_3_monthlyprice AS double))) ELSE 0E0 END)) max_estimatedmonthlysavings_value_medium
   , CONCAT(COALESCE(recommendationoptions_3_performancerisk, 'na'), ';', COALESCE(recommendationoptions_3_configuration_volumetype, 'na'), ';', COALESCE(recommendationoptions_3_configuration_volumesize, 'na'), ';', COALESCE(recommendationoptions_3_configuration_volumebaselineiops, 'na'), ';', COALESCE(recommendationoptions_3_configuration_volumebaselinethroughput, 'na'), ';', COALESCE(recommendationoptions_3_configuration_volumeburstiops, 'na'), ';', COALESCE(recommendationoptions_3_configuration_volumeburstthroughput, 'na'), ';') option_details
   , tags tags
   FROM
     compute_optimizer_ebs_volume_lines
   WHERE ((volumearn LIKE '%arn:%') AND (recommendationoptions_3_configuration_volumetype <> ''))
) 