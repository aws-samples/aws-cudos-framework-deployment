CREATE OR REPLACE VIEW compute_optimizer_ebs_volume_options AS (
SELECT
    TRY(date_parse(lastrefreshtimestamp_utc,'%Y-%m-%d %H:%i:%s')) as lastrefreshtimestamp_utc,
    accountid as accountid,
    volumearn as arn,
    try(split_part(volumearn, ':', 4)) as region,
    try(split_part(volumearn, ':', 3)) as service,
    try(split_part(volumearn, ':', 7)) as name,
    'ebs_volume' as module,
    'ebs_volume' as recommendationsourcetype,
    finding as finding,
    cast ('' as varchar) as reason,
    lookbackperiodindays as lookbackperiodindays,
    currentperformancerisk as currentperformancerisk,
    errorcode as errorcode,
    errormessage as errormessage,
    cast ('' as varchar) as ressouce_details,

    CONCAT(
        utilizationmetrics_volumereadopspersecondmaximum, ';',
        utilizationmetrics_volumewriteopspersecondmaximum, ';',
        utilizationmetrics_volumereadbytespersecondmaximum, ';',
        utilizationmetrics_volumewritebytespersecondmaximum, ';'
    ) as utilizationmetrics,

    'Current' as option_name,
    currentconfiguration_volumetype as option_from,
    cast ('' as varchar) as option_to,
    recommendationoptions_1_estimatedmonthlysavings_currency as currency,
    try_cast(current_monthlyprice as double) as monthlyprice,
    try(cast(current_monthlyprice as double) / 730  ) as hourlyprice,
    0.0 as estimatedmonthlysavings_value,
    0.0 as estimatedmonthly_ondemand_cost_change,

    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_low,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium,

    CONCAT(
        currentperformancerisk, ';', --  as performancerisk
        currentconfiguration_volumetype, ';', --  as volumetype
        currentconfiguration_volumesize, ';', --  as volumesize
        currentconfiguration_volumebaselineiops, ';', --  as volumebaselineiops
        currentconfiguration_volumebaselinethroughput, ';', --  as volumebaselinethroughput
        currentconfiguration_volumeburstiops, ';', --  as volumeburstiops
        currentconfiguration_volumeburstthroughput, ';' --  as volumeburstthroughput
    ) as option_details

FROM
    compute_optimizer_ebs_volume_lines
WHERE
    volumearn LIKE '%arn:%'

UNION SELECT
    TRY(date_parse(lastrefreshtimestamp_utc,'%Y-%m-%d %H:%i:%s')) as lastrefreshtimestamp_utc,
    accountid as accountid,
    volumearn as arn,
    try(split_part(volumearn, ':', 4)) as region,
    try(split_part(volumearn, ':', 3)) as service,
    try(split_part(volumearn, ':', 7)) as name,
    'ebs_volume' as module,
    'ebs_volume' as recommendationsourcetype,
    finding as finding,
    cast ('' as varchar) as reason,
    lookbackperiodindays as lookbackperiodindays,
    currentperformancerisk as currentperformancerisk,
    errorcode as errorcode,
    errormessage as errormessage,
    cast ('' as varchar) as ressouce_details,
    cast ('' as varchar) as utilizationmetrics,

    'Option 1' as option_name,
    currentconfiguration_volumetype as option_from,
    recommendationoptions_1_configuration_volumetype as option_to,
    recommendationoptions_1_estimatedmonthlysavings_currency as currency,
    try_cast(recommendationoptions_1_monthlyprice as double) as monthlyprice,
    try(cast(recommendationoptions_1_monthlyprice as double) / 730  ) as hourlyprice,
    try_cast(recommendationoptions_1_estimatedmonthlysavings_value as double) as estimatedmonthlysavings_value,
    try( cast(current_monthlyprice as double) -
         cast(recommendationoptions_1_monthlyprice as double) ) as estimatedmonthly_ondemand_cost_change,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_low,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium,

    CONCAT(
        recommendationoptions_1_performancerisk, ';', -- as performancerisk,
        recommendationoptions_1_configuration_volumetype, ';', -- as volumetype,
        recommendationoptions_1_configuration_volumesize, ';', -- as volumesize,
        recommendationoptions_1_configuration_volumebaselineiops, ';', -- as volumebaselineiops,
        recommendationoptions_1_configuration_volumebaselinethroughput, ';', -- as volumebaselinethroughput,
        recommendationoptions_1_configuration_volumeburstiops, ';', -- as volumeburstiops,
        recommendationoptions_1_configuration_volumeburstthroughput, ';' -- as volumeburstthroughput,
    ) as option_details

FROM
    compute_optimizer_ebs_volume_lines
WHERE
    volumearn LIKE '%arn:%'
  AND recommendationoptions_1_estimatedmonthlysavings_currency <> ''


UNION SELECT
    TRY(date_parse(lastrefreshtimestamp_utc,'%Y-%m-%d %H:%i:%s')) as lastrefreshtimestamp_utc,
    accountid as accountid,
    volumearn as arn,
    try(split_part(volumearn, ':', 4)) as region,
    try(split_part(volumearn, ':', 3)) as service,
    try(split_part(volumearn, ':', 7)) as name,
    'ebs_volume' as module,
    'ebs_volume' as recommendationsourcetype,
    finding as finding,
    cast ('' as varchar) as reason,
    lookbackperiodindays as lookbackperiodindays,
    currentperformancerisk as currentperformancerisk,
    errorcode as errorcode,
    errormessage as errormessage,
    cast ('' as varchar) as ressouce_details,
    cast ('' as varchar) as utilizationmetrics,

    'Option 2' as option_name,
    currentconfiguration_volumetype as option_from,
    recommendationoptions_2_configuration_volumetype as option_to,
    recommendationoptions_2_estimatedmonthlysavings_currency as currency,
    try_cast(recommendationoptions_2_monthlyprice as double) as monthlyprice,
    try(cast(recommendationoptions_2_monthlyprice as double) / 730  ) as hourlyprice,
    try_cast(recommendationoptions_2_estimatedmonthlysavings_value as double) as estimatedmonthlysavings_value,
    try( cast(current_monthlyprice as double) -
         cast(recommendationoptions_2_monthlyprice as double) ) as estimatedmonthly_ondemand_cost_change,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_low,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium,


    CONCAT(
        recommendationoptions_2_performancerisk, ';', -- as performancerisk,
        recommendationoptions_2_configuration_volumetype, ';', -- as volumetype,
        recommendationoptions_2_configuration_volumesize, ';', -- as volumesize,
        recommendationoptions_2_configuration_volumebaselineiops, ';', -- as volumebaselineiops,
        recommendationoptions_2_configuration_volumebaselinethroughput, ';', -- as volumebaselinethroughput,
        recommendationoptions_2_configuration_volumeburstiops, ';', -- as volumeburstiops,
        recommendationoptions_2_configuration_volumeburstthroughput, ';' -- as volumeburstthroughput,
    ) as option_details

FROM
    compute_optimizer_ebs_volume_lines
WHERE
    volumearn LIKE '%arn:%'
  AND recommendationoptions_2_estimatedmonthlysavings_currency <> ''

  UNION SELECT
    TRY(date_parse(lastrefreshtimestamp_utc,'%Y-%m-%d %H:%i:%s')) as lastrefreshtimestamp_utc,
    accountid as accountid,
    volumearn as arn,
    try(split_part(volumearn, ':', 4)) as region,
    try(split_part(volumearn, ':', 3)) as service,
    try(split_part(volumearn, ':', 7)) as name,
    'ebs_volume' as module,
    'ebs_volume' as recommendationsourcetype,
    finding as finding,
    cast ('' as varchar) as reason,
    lookbackperiodindays as lookbackperiodindays,
    currentperformancerisk as currentperformancerisk,
    errorcode as errorcode,
    errormessage as errormessage,
    cast ('' as varchar) as ressouce_details,
    cast ('' as varchar) as utilizationmetrics,


    'Option 3' as option_name,
    currentconfiguration_volumetype as option_from,
    recommendationoptions_3_configuration_volumetype as option_to,
    recommendationoptions_3_estimatedmonthlysavings_currency as currency,
    try_cast(recommendationoptions_3_monthlyprice as double) as monthlyprice,
    try(cast(recommendationoptions_3_monthlyprice as double) / 730  ) as hourlyprice,
    try_cast(recommendationoptions_3_estimatedmonthlysavings_value as double) as estimatedmonthlysavings_value,
    try( cast(current_monthlyprice as double) -
         cast(recommendationoptions_3_monthlyprice as double) ) as estimatedmonthly_ondemand_cost_change,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_low,
    GREATEST(
        CASE WHEN recommendationoptions_1_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_1_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_1_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_2_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_2_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_2_monthlyprice as double) )
             ELSE 0E0 END,
        CASE WHEN recommendationoptions_3_estimatedmonthlysavings_value != '' THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)
             WHEN recommendationoptions_3_monthlyprice != ''                  THEN  try( cast(current_monthlyprice as double) - cast(recommendationoptions_3_monthlyprice as double) )
             ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium,

    CONCAT(
        recommendationoptions_3_performancerisk, ';', -- as performancerisk,
        recommendationoptions_3_configuration_volumetype, ';', -- as volumetype,
        recommendationoptions_3_configuration_volumesize, ';', -- as volumesize,
        recommendationoptions_3_configuration_volumebaselineiops, ';', -- as volumebaselineiops,
        recommendationoptions_3_configuration_volumebaselinethroughput, ';', -- as volumebaselinethroughput,
        recommendationoptions_3_configuration_volumeburstiops, ';', -- as volumeburstiops,
        recommendationoptions_3_configuration_volumeburstthroughput, ';' -- as volumeburstthroughput,
    ) as option_details

FROM
    compute_optimizer_ebs_volume_lines
WHERE
    volumearn LIKE '%arn:%'
  AND recommendationoptions_3_estimatedmonthlysavings_currency <> ''
)