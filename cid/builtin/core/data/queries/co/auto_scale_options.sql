CREATE OR REPLACE VIEW compute_optimizer_auto_scale_options AS

SELECT * FROM (

    SELECT

     TRY("date_parse"(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
   , accountid accountid
   , autoscalinggrouparn arn
   , TRY("split_part"(autoscalinggrouparn, ':', 4)) region
   , TRY("split_part"(autoscalinggrouparn, ':', 3)) service
   , autoscalinggroupname name
   , 'auto_scale' module
   , 'auto_scale' recommendationsourcetype
   , finding finding
   , cast ('' as varchar) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk as currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CONCAT(
        inferredworkloadtypes, ';',
        effectiverecommendationpreferencesenhancedinfrastructuremetrics
    ) ressouce_details
   , CONCAT(
         utilizationmetrics_disk_read_bytes_per_second_maximum, ';',
         utilizationmetrics_disk_read_ops_per_second_maximum, ';',
         utilizationmetrics_disk_write_bytes_per_second_maximum, ';',
         utilizationmetrics_disk_write_ops_per_second_maximum, ';',
         utilizationmetrics_ebs_read_bytes_per_second_maximum, ';',
         utilizationmetrics_ebs_read_ops_per_second_maximum, ';',
         utilizationmetrics_ebs_write_bytes_per_second_maximum, ';',
         utilizationmetrics_ebs_write_ops_per_second_maximum, ';',
         utilizationmetrics_network_in_bytes_per_second_maximum, ';',
         utilizationmetrics_network_out_bytes_per_second_maximum, ';',
         utilizationmetrics_network_packets_in_per_second_maximum, ';',
         utilizationmetrics_network_packets_out_per_second_maximum, ';'
     ) utilizationmetrics
   , 'Current' option_name
   , currentconfiguration_instancetype option_from
   , '' option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , TRY(CAST(current_ondemandprice AS double) * 730) monthlyprice
   , TRY(CAST(current_ondemandprice AS double)) hourlyprice
   , 0E0 estimatedmonthlysavings_value
   , 0E0 estimatedmonthly_ondemand_cost_change
   , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow' )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow' )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow' )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low

    , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow'
               OR recommendationoptions_1_migrationeffort = 'Low'    )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow'
               OR recommendationoptions_2_migrationeffort = 'Low'    )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow'
               OR recommendationoptions_3_migrationeffort = 'Low'    )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
      ) as max_estimatedmonthlysavings_value_low
    , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow'
               OR recommendationoptions_1_migrationeffort = 'Low'
               OR recommendationoptions_1_migrationeffort = 'Medium'    )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow'
               OR recommendationoptions_2_migrationeffort = 'Low'
               OR recommendationoptions_2_migrationeffort = 'Medium'    )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow'
               OR recommendationoptions_3_migrationeffort = 'Low'
               OR recommendationoptions_3_migrationeffort = 'Medium'    )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium

   , CONCAT(
         currentperformancerisk, ';',
         currentconfiguration_instancetype, ';',
         '', ';',
         current_memory, ';',
         current_vcpus, ';',
         current_network, ';',
         current_storage, ';',
         '', ';',
         utilizationmetrics_cpu_maximum, ';',
         utilizationmetrics_memory_maximum, ';',
         currentconfiguration_desiredcapacity, ';'

       ) option_details

    FROM
        compute_optimizer_auto_scale_lines
    WHERE
        autoscalinggrouparn LIKE '%arn:%'

UNION SELECT

     TRY("date_parse"(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
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
   , currentperformancerisk as currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CONCAT(
        inferredworkloadtypes, ';',
        effectiverecommendationpreferencesenhancedinfrastructuremetrics
    ) ressouce_details
   , CONCAT(
         utilizationmetrics_disk_read_bytes_per_second_maximum, ';',
         utilizationmetrics_disk_read_ops_per_second_maximum, ';',
         utilizationmetrics_disk_write_bytes_per_second_maximum, ';',
         utilizationmetrics_disk_write_ops_per_second_maximum, ';',
         utilizationmetrics_ebs_read_bytes_per_second_maximum, ';',
         utilizationmetrics_ebs_read_ops_per_second_maximum, ';',
         utilizationmetrics_ebs_write_bytes_per_second_maximum, ';',
         utilizationmetrics_ebs_write_ops_per_second_maximum, ';',
         utilizationmetrics_network_in_bytes_per_second_maximum, ';',
         utilizationmetrics_network_out_bytes_per_second_maximum, ';',
         utilizationmetrics_network_packets_in_per_second_maximum, ';',
         utilizationmetrics_network_packets_out_per_second_maximum, ';'
     ) utilizationmetrics
   , 'Option 1' option_name
   , currentconfiguration_instancetype option_from
   , recommendationoptions_1_configuration_instancetype option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , TRY(CAST(recommendationoptions_1_ondemandprice AS double) * 730) monthlyprice
   , TRY(CAST(recommendationoptions_1_ondemandprice AS double)) hourlyprice
   , TRY(CAST(recommendationoptions_1_estimatedmonthlysavings_value as double)) as estimatedmonthlysavings_value
   , TRY((CAST(current_ondemandprice as double) - CAST(recommendationoptions_1_ondemandprice as double)) * 730) as estimatedmonthly_ondemand_cost_change
   , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow' )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow' )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow' )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low

    , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow'
               OR recommendationoptions_1_migrationeffort = 'Low'    )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow'
               OR recommendationoptions_2_migrationeffort = 'Low'    )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow'
               OR recommendationoptions_3_migrationeffort = 'Low'    )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
      ) as max_estimatedmonthlysavings_value_low
    , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow'
               OR recommendationoptions_1_migrationeffort = 'Low'
               OR recommendationoptions_1_migrationeffort = 'Medium'    )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow'
               OR recommendationoptions_2_migrationeffort = 'Low'
               OR recommendationoptions_2_migrationeffort = 'Medium'    )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow'
               OR recommendationoptions_3_migrationeffort = 'Low'
               OR recommendationoptions_3_migrationeffort = 'Medium'    )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium
   , CONCAT(
         recommendationoptions_1_performancerisk, ';',
         recommendationoptions_1_configuration_instancetype, ';',
         recommendationoptions_1_migrationeffort, ';',
         recommendationoptions_1_memory, ';',
         recommendationoptions_1_vcpus, ';',
         recommendationoptions_1_network, ';',
         recommendationoptions_1_storage, ';',
         '', ';', --platform diff
         recommendationoptions_1_projectedutilizationmetrics_cpu_maximum, ';',
         recommendationoptions_1_projectedutilizationmetrics_memory_maximum, ';',
         recommendationoptions_1_configuration_desiredcapacity, ';'

       ) option_details

    FROM
        compute_optimizer_auto_scale_lines
    WHERE
        autoscalinggrouparn LIKE '%arn:%'


UNION SELECT

     TRY("date_parse"(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
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
   , currentperformancerisk as currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CONCAT(
        inferredworkloadtypes, ';',
        effectiverecommendationpreferencesenhancedinfrastructuremetrics
    ) ressouce_details
   , CONCAT(
         utilizationmetrics_disk_read_bytes_per_second_maximum, ';',
         utilizationmetrics_disk_read_ops_per_second_maximum, ';',
         utilizationmetrics_disk_write_bytes_per_second_maximum, ';',
         utilizationmetrics_disk_write_ops_per_second_maximum, ';',
         utilizationmetrics_ebs_read_bytes_per_second_maximum, ';',
         utilizationmetrics_ebs_read_ops_per_second_maximum, ';',
         utilizationmetrics_ebs_write_bytes_per_second_maximum, ';',
         utilizationmetrics_ebs_write_ops_per_second_maximum, ';',
         utilizationmetrics_network_in_bytes_per_second_maximum, ';',
         utilizationmetrics_network_out_bytes_per_second_maximum, ';',
         utilizationmetrics_network_packets_in_per_second_maximum, ';',
         utilizationmetrics_network_packets_out_per_second_maximum, ';'
     ) utilizationmetrics
   , 'Option 2' option_name
   , currentconfiguration_instancetype option_from
   , recommendationoptions_2_configuration_instancetype option_to
   , recommendationoptions_2_estimatedmonthlysavings_currency currency
   , TRY(CAST(recommendationoptions_2_ondemandprice AS double) * 730) monthlyprice
   , TRY(CAST(recommendationoptions_2_ondemandprice AS double)) hourlyprice
   , TRY(CAST(recommendationoptions_2_estimatedmonthlysavings_value as double)) as estimatedmonthlysavings_value
   , TRY((CAST(current_ondemandprice as double) - CAST(recommendationoptions_2_ondemandprice as double)) * 730) as estimatedmonthly_ondemand_cost_change
   , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow' )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow' )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow' )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low

    , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow'
               OR recommendationoptions_1_migrationeffort = 'Low'    )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow'
               OR recommendationoptions_2_migrationeffort = 'Low'    )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow'
               OR recommendationoptions_3_migrationeffort = 'Low'    )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
      ) as max_estimatedmonthlysavings_value_low
    , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow'
               OR recommendationoptions_1_migrationeffort = 'Low'
               OR recommendationoptions_1_migrationeffort = 'Medium'    )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow'
               OR recommendationoptions_2_migrationeffort = 'Low'
               OR recommendationoptions_2_migrationeffort = 'Medium'    )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow'
               OR recommendationoptions_3_migrationeffort = 'Low'
               OR recommendationoptions_3_migrationeffort = 'Medium'    )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium

   , CONCAT(
         recommendationoptions_2_performancerisk, ';',
         recommendationoptions_2_configuration_instancetype, ';',
         recommendationoptions_2_migrationeffort, ';',
         recommendationoptions_2_memory, ';',
         recommendationoptions_2_vcpus, ';',
         recommendationoptions_2_network, ';',
         recommendationoptions_2_storage, ';',
         '', ';', --platform diff
         recommendationoptions_2_projectedutilizationmetrics_cpu_maximum, ';',
         recommendationoptions_2_projectedutilizationmetrics_memory_maximum, ';',
         recommendationoptions_2_configuration_desiredcapacity, ';'

       ) option_details

    FROM
        compute_optimizer_auto_scale_lines
    WHERE
        autoscalinggrouparn LIKE '%arn:%'
    AND recommendationoptions_2_estimatedmonthlysavings_currency <> ''


UNION SELECT

     TRY("date_parse"(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
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
   , currentperformancerisk as currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CONCAT(
        inferredworkloadtypes, ';',
        effectiverecommendationpreferencesenhancedinfrastructuremetrics
    ) ressouce_details
   , CONCAT(
         utilizationmetrics_disk_read_bytes_per_second_maximum, ';',
         utilizationmetrics_disk_read_ops_per_second_maximum, ';',
         utilizationmetrics_disk_write_bytes_per_second_maximum, ';',
         utilizationmetrics_disk_write_ops_per_second_maximum, ';',
         utilizationmetrics_ebs_read_bytes_per_second_maximum, ';',
         utilizationmetrics_ebs_read_ops_per_second_maximum, ';',
         utilizationmetrics_ebs_write_bytes_per_second_maximum, ';',
         utilizationmetrics_ebs_write_ops_per_second_maximum, ';',
         utilizationmetrics_network_in_bytes_per_second_maximum, ';',
         utilizationmetrics_network_out_bytes_per_second_maximum, ';',
         utilizationmetrics_network_packets_in_per_second_maximum, ';',
         utilizationmetrics_network_packets_out_per_second_maximum, ';'
     ) utilizationmetrics
   , 'Option 3' option_name
   , currentconfiguration_instancetype option_from
   , recommendationoptions_3_configuration_instancetype option_to
   , recommendationoptions_3_estimatedmonthlysavings_currency currency
   , TRY(CAST(recommendationoptions_3_ondemandprice AS double) * 730) monthlyprice
   , TRY(CAST(recommendationoptions_3_ondemandprice AS double)) hourlyprice
   , TRY(CAST(recommendationoptions_3_estimatedmonthlysavings_value as double)) as estimatedmonthlysavings_value
   , TRY((CAST(current_ondemandprice as double) - CAST(recommendationoptions_3_ondemandprice as double)) * 730) as estimatedmonthly_ondemand_cost_change
   , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow' )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow' )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow' )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_very_low

    , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow'
               OR recommendationoptions_1_migrationeffort = 'Low'    )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow'
               OR recommendationoptions_2_migrationeffort = 'Low'    )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow'
               OR recommendationoptions_3_migrationeffort = 'Low'    )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
      ) as max_estimatedmonthlysavings_value_low
    , GREATEST(
       CASE WHEN((recommendationoptions_1_migrationeffort = ''
               OR recommendationoptions_1_migrationeffort = 'VeryLow'
               OR recommendationoptions_1_migrationeffort = 'Low'
               OR recommendationoptions_1_migrationeffort = 'Medium'    )
              AND recommendationoptions_1_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_2_migrationeffort = ''
               OR recommendationoptions_2_migrationeffort = 'VeryLow'
               OR recommendationoptions_2_migrationeffort = 'Low'
               OR recommendationoptions_2_migrationeffort = 'Medium'    )
              AND recommendationoptions_2_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value as double) ELSE 0E0 END,
       CASE WHEN((recommendationoptions_3_migrationeffort = ''
               OR recommendationoptions_3_migrationeffort = 'VeryLow'
               OR recommendationoptions_3_migrationeffort = 'Low'
               OR recommendationoptions_3_migrationeffort = 'Medium'    )
              AND recommendationoptions_3_estimatedmonthlysavings_currency != '') THEN TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value as double) ELSE 0E0 END
    ) as max_estimatedmonthlysavings_value_medium
   , CONCAT(
         recommendationoptions_3_performancerisk, ';',
         recommendationoptions_3_configuration_instancetype, ';',
         recommendationoptions_3_migrationeffort, ';',
         recommendationoptions_3_memory, ';',
         recommendationoptions_3_vcpus, ';',
         recommendationoptions_3_network, ';',
         recommendationoptions_3_storage, ';',
         '', ';', --platform diff
         recommendationoptions_3_projectedutilizationmetrics_cpu_maximum, ';',
         recommendationoptions_3_projectedutilizationmetrics_memory_maximum, ';',
         recommendationoptions_3_configuration_desiredcapacity, ';'

       ) option_details

    FROM
        compute_optimizer_auto_scale_lines
    WHERE
        autoscalinggrouparn LIKE '%arn:%'
    AND recommendationoptions_3_estimatedmonthlysavings_currency <> ''
)
