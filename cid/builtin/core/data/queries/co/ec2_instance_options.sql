CREATE OR REPLACE VIEW compute_optimizer_ec2_instance_options AS
(
   SELECT
     TRY("date_parse"(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
   , accountid accountid
   , instancearn arn
   , TRY("split_part"(instancearn, ':', 4)) region
   , TRY("split_part"(instancearn, ':', 3)) service
   , instancename name
   , 'ec2_instance' module
   , recommendationssources_1_recommendationsourcetype recommendationsourcetype
   , finding finding
   , CONCAT(
        (CASE WHEN (findingreasoncodes_iscpuoverprovisioned =               'true') THEN 'CPU-Over '               ELSE '' END),
        (CASE WHEN (findingreasoncodes_iscpuunderprovisioned =              'true') THEN 'CPU-Under '              ELSE '' END),
        (CASE WHEN (findingreasoncodes_isdiskiopsoverprovisioned =          'true') THEN 'DiskIOPS-Over '          ELSE '' END),
        (CASE WHEN (findingreasoncodes_isdiskiopsunderprovisioned =         'true') THEN 'DiskIOPS-Under '         ELSE '' END),
        (CASE WHEN (findingreasoncodes_isdiskthroughputoverprovisioned =    'true') THEN 'DiskThroughput-Over '    ELSE '' END),
        (CASE WHEN (findingreasoncodes_isdiskthroughputunderprovisioned =   'true') THEN 'DiskThroughput-Under '   ELSE '' END),
        (CASE WHEN (findingreasoncodes_isebsiopsoverprovisioned =           'true') THEN 'EBSIOPS-Over '           ELSE '' END),
        (CASE WHEN (findingreasoncodes_isebsiopsunderprovisioned =          'true') THEN 'EBSIOPS-Under '          ELSE '' END),
        (CASE WHEN (findingreasoncodes_isebsthroughputoverprovisioned =     'true') THEN 'EBSThroughput-Over '     ELSE '' END),
        (CASE WHEN (findingreasoncodes_isebsthroughputunderprovisioned =    'true') THEN 'EBSThroughput-Under '    ELSE '' END),
        (CASE WHEN (findingreasoncodes_ismemoryoverprovisioned =            'true') THEN 'Memory-Over '            ELSE '' END),
        (CASE WHEN (findingreasoncodes_ismemoryunderprovisioned =           'true') THEN 'Memory-Under '           ELSE '' END),
        (CASE WHEN (findingreasoncodes_isnetworkbandwidthoverprovisioned =  'true') THEN 'NetworkBandwidth-Over '  ELSE '' END),
        (CASE WHEN (findingreasoncodes_isnetworkbandwidthunderprovisioned = 'true') THEN 'NetworkBandwidth-Under ' ELSE '' END),
        (CASE WHEN (findingreasoncodes_isnetworkppsoverprovisioned =        'true') THEN 'NetworkPPS-Over '        ELSE '' END),
        (CASE WHEN (findingreasoncodes_isnetworkppsunderprovisioned =       'true') THEN 'NetworkPPS-Under '       ELSE '' END)
    ) reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk as currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , CONCAT(effectiverecommendationpreferencesenhancedinfrastructuremetrics, ';',
         inferredworkloadtypes, ';') ressouce_details
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
         utilizationmetrics_network_packets_out_per_second_maximum, ';') utilizationmetrics
   , 'Current' option_name
    , currentinstancetype option_from
   , '' option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , TRY((CAST(current_ondemandprice AS double) * 730)) monthlyprice
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
         currentinstancetype, ';',
         '', ';',
         current_memory, ';',
         current_vcpus, ';',
         current_network, ';',
         current_storage, ';',
         '', ';',
         utilizationmetrics_cpu_maximum, ';',
         utilizationmetrics_memory_maximum, ';'
       ) option_details
   FROM
     compute_optimizer_ec2_instance_lines
   WHERE (instancearn LIKE '%arn:%')
UNION SELECT
     TRY("date_parse"(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
   , accountid accountid
   , instancearn arn
   , TRY("split_part"(instancearn, ':', 4)) region
   , TRY("split_part"(instancearn, ':', 3)) service
   , instancename name
   , 'ec2_instance' module
   , recommendationssources_1_recommendationsourcetype recommendationsourcetype
   , finding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk as currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , '' ressouce_details
   , '' utilizationmetrics
   , 'Option 1' option_name
   , currentinstancetype option_from
   , recommendationoptions_1_instancetype option_to
   , recommendationoptions_1_estimatedmonthlysavings_currency currency
   , TRY((CAST(recommendationoptions_1_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(recommendationoptions_1_ondemandprice AS double)) hourlyprice
   , TRY_CAST(recommendationoptions_1_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_1_ondemandprice AS double)) * 730)) estimatedmonthly_ondemand_cost_change
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
         recommendationoptions_1_instancetype, ';',
         recommendationoptions_1_migrationeffort, ';',
         recommendationoptions_1_memory, ';',
         recommendationoptions_1_vcpus, ';',
         recommendationoptions_1_network, ';',
         recommendationoptions_1_storage, ';',
         CONCAT(
            (CASE WHEN (recommendationoptions_1_platformdifferences_isarchitecturedifferent = 'true') THEN 'Architecture ' ELSE '' END),
            (CASE WHEN (recommendationoptions_1_platformdifferences_ishypervisordifferent = 'true') THEN 'Hypervisor ' ELSE '' END),
            (CASE WHEN (recommendationoptions_1_platformdifferences_isinstancestoreavailabilitydifferent = 'true') THEN 'InstanceStoreAvailability ' ELSE '' END),
            (CASE WHEN (recommendationoptions_1_platformdifferences_isnetworkinterfacedifferent = 'true') THEN 'NetworkInterface ' ELSE '' END),
            (CASE WHEN (recommendationoptions_1_platformdifferences_isstorageinterfacedifferent = 'true') THEN 'StorageInterface ' ELSE '' END),
            (CASE WHEN (recommendationoptions_1_platformdifferences_isvirtualizationtypedifferent = 'true') THEN 'VirtualizationType ' ELSE '' END)
         ), ';',
         recommendationoptions_1_projectedutilizationmetrics_cpu_maximum, ';',
         recommendationoptions_1_projectedutilizationmetrics_memory_maximum, ';'
       ) option_details
   FROM
     compute_optimizer_ec2_instance_lines
   WHERE (instancearn LIKE '%arn:%')
UNION SELECT
     TRY("date_parse"(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
   , accountid accountid
   , instancearn arn
   , TRY("split_part"(instancearn, ':', 4)) region
   , TRY("split_part"(instancearn, ':', 3)) service
   , instancename name
   , 'ec2_instance' module
   , recommendationssources_1_recommendationsourcetype recommendationsourcetype
   , finding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk as currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , '' ressouce_details
   , '' utilizationmetrics
   , 'Option 2' option_name
   , currentinstancetype option_from
   , recommendationoptions_2_instancetype option_to
   , recommendationoptions_2_estimatedmonthlysavings_currency currency
   , TRY((CAST(recommendationoptions_2_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(recommendationoptions_2_ondemandprice AS double)) hourlyprice
   , TRY_CAST(recommendationoptions_2_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_2_ondemandprice AS double)) * 730)) estimatedmonthly_ondemand_cost_change
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
         recommendationoptions_2_instancetype, ';',
         recommendationoptions_2_migrationeffort, ';',
         recommendationoptions_2_memory, ';',
         recommendationoptions_2_vcpus, ';',
         recommendationoptions_2_network, ';',
         recommendationoptions_2_storage, ';',
         CONCAT(
            (CASE WHEN (recommendationoptions_2_platformdifferences_isarchitecturedifferent = 'true') THEN 'Architecture ' ELSE '' END),
            (CASE WHEN (recommendationoptions_2_platformdifferences_ishypervisordifferent = 'true') THEN 'Hypervisor ' ELSE '' END),
            (CASE WHEN (recommendationoptions_2_platformdifferences_isinstancestoreavailabilitydifferent = 'true') THEN 'InstanceStoreAvailability ' ELSE '' END),
            (CASE WHEN (recommendationoptions_2_platformdifferences_isnetworkinterfacedifferent = 'true') THEN 'NetworkInterface ' ELSE '' END),
            (CASE WHEN (recommendationoptions_2_platformdifferences_isstorageinterfacedifferent = 'true') THEN 'StorageInterface ' ELSE '' END),
            (CASE WHEN (recommendationoptions_2_platformdifferences_isvirtualizationtypedifferent = 'true') THEN 'VirtualizationType ' ELSE '' END)
         ), ';',
         recommendationoptions_2_projectedutilizationmetrics_cpu_maximum, ';',
         recommendationoptions_2_projectedutilizationmetrics_memory_maximum, ';'
   ) option_details
   FROM
     compute_optimizer_ec2_instance_lines
   WHERE (instancearn LIKE '%arn:%')
   AND recommendationoptions_2_estimatedmonthlysavings_currency <> ''

UNION SELECT
     TRY("date_parse"(lastrefreshtimestamp_utc, '%Y-%m-%d %H:%i:%s')) lastrefreshtimestamp_utc
   , accountid accountid
   , instancearn arn
   , TRY("split_part"(instancearn, ':', 4)) region
   , TRY("split_part"(instancearn, ':', 3)) service
   , instancename name
   , 'ec2_instance' module
   , recommendationssources_1_recommendationsourcetype recommendationsourcetype
   , finding finding
   , '' reason
   , lookbackperiodindays lookbackperiodindays
   , currentperformancerisk as currentperformancerisk
   , errorcode errorcode
   , errormessage errormessage
   , '' ressouce_details
   , '' utilizationmetrics
   , 'Option 3' option_name
   , currentinstancetype option_from
   , recommendationoptions_3_instancetype option_to
   , recommendationoptions_3_estimatedmonthlysavings_currency currency
   , TRY((CAST(recommendationoptions_3_ondemandprice AS double) * 730)) monthlyprice
   , TRY(CAST(recommendationoptions_3_ondemandprice AS double)) hourlyprice
   , TRY_CAST(recommendationoptions_3_estimatedmonthlysavings_value AS double) estimatedmonthlysavings_value
   , TRY(((CAST(current_ondemandprice AS double) - CAST(recommendationoptions_3_ondemandprice AS double)) * 730)) estimatedmonthly_ondemand_cost_change
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
         recommendationoptions_3_instancetype, ';',
         recommendationoptions_3_migrationeffort, ';',
         recommendationoptions_3_memory, ';',
         recommendationoptions_3_vcpus, ';',
         recommendationoptions_3_network, ';',
         recommendationoptions_3_storage, ';',
         CONCAT(
            (CASE WHEN (recommendationoptions_3_platformdifferences_isarchitecturedifferent = 'true') THEN 'Architecture ' ELSE '' END),
            (CASE WHEN (recommendationoptions_3_platformdifferences_ishypervisordifferent = 'true') THEN 'Hypervisor ' ELSE '' END),
            (CASE WHEN (recommendationoptions_3_platformdifferences_isinstancestoreavailabilitydifferent = 'true') THEN 'InstanceStoreAvailability ' ELSE '' END),
            (CASE WHEN (recommendationoptions_3_platformdifferences_isnetworkinterfacedifferent = 'true') THEN 'NetworkInterface ' ELSE '' END),
            (CASE WHEN (recommendationoptions_3_platformdifferences_isstorageinterfacedifferent = 'true') THEN 'StorageInterface ' ELSE '' END),
            (CASE WHEN (recommendationoptions_3_platformdifferences_isvirtualizationtypedifferent = 'true') THEN 'VirtualizationType ' ELSE '' END)
         ), ';',
         recommendationoptions_3_projectedutilizationmetrics_cpu_maximum, ';',
         recommendationoptions_3_projectedutilizationmetrics_memory_maximum, ';'
       ) option_details
   FROM
     compute_optimizer_ec2_instance_lines
   WHERE (instancearn LIKE '%arn:%')
     AND recommendationoptions_3_estimatedmonthlysavings_currency <> ''

)