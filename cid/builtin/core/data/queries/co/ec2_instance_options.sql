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
        COALESCE(currentperformancerisk, 'na'), ';',
        COALESCE(currentinstancetype, 'na'), ';',
        COALESCE('', 'na'), ';',
        COALESCE(current_memory, 'na'), ';',
        COALESCE(current_vcpus, 'na'), ';',
        COALESCE(current_network, 'na'), ';',
        COALESCE(current_storage, 'na'), ';',
        COALESCE('', 'na'), ';',
        COALESCE(utilizationmetrics_cpu_maximum, 'na'), ';',
        COALESCE(utilizationmetrics_memory_maximum, 'na'), ';'
   ) option_details
   , tags tags
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
        COALESCE(recommendationoptions_1_performancerisk, 'na'), ';',
        COALESCE(recommendationoptions_1_instancetype, 'na'), ';',
        COALESCE(recommendationoptions_1_migrationeffort, 'na'), ';',
        COALESCE(recommendationoptions_1_memory, 'na'), ';',
        COALESCE(recommendationoptions_1_vcpus, 'na'), ';',
        COALESCE(recommendationoptions_1_network, 'na'), ';',
        COALESCE(recommendationoptions_1_storage, 'na'), ';',
        CONCAT(
           (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_isarchitecturedifferent, 'na') = 'true') THEN 'Architecture ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_ishypervisordifferent, 'na') = 'true') THEN 'Hypervisor ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_isinstancestoreavailabilitydifferent, 'na') = 'true') THEN 'InstanceStoreAvailability ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_isnetworkinterfacedifferent, 'na') = 'true') THEN 'NetworkInterface ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_isstorageinterfacedifferent, 'na') = 'true') THEN 'StorageInterface ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_1_platformdifferences_isvirtualizationtypedifferent, 'na') = 'true') THEN 'VirtualizationType ' ELSE '' END)
        ), ';',
        COALESCE(recommendationoptions_1_projectedutilizationmetrics_cpu_maximum, 'na'), ';',
        COALESCE(recommendationoptions_1_projectedutilizationmetrics_memory_maximum, 'na'), ';'
   ) option_details
   , tags tags
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
        COALESCE(recommendationoptions_2_performancerisk, 'na'), ';',
        COALESCE(recommendationoptions_2_instancetype, 'na'), ';',
        COALESCE(recommendationoptions_2_migrationeffort, 'na'), ';',
        COALESCE(recommendationoptions_2_memory, 'na'), ';',
        COALESCE(recommendationoptions_2_vcpus, 'na'), ';',
        COALESCE(recommendationoptions_2_network, 'na'), ';',
        COALESCE(recommendationoptions_2_storage, 'na'), ';',
        CONCAT(
           (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_isarchitecturedifferent, 'na') = 'true') THEN 'Architecture ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_ishypervisordifferent, 'na') = 'true') THEN 'Hypervisor ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_isinstancestoreavailabilitydifferent, 'na') = 'true') THEN 'InstanceStoreAvailability ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_isnetworkinterfacedifferent, 'na') = 'true') THEN 'NetworkInterface ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_isstorageinterfacedifferent, 'na') = 'true') THEN 'StorageInterface ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_2_platformdifferences_isvirtualizationtypedifferent, 'na') = 'true') THEN 'VirtualizationType ' ELSE '' END)
        ), ';',
        COALESCE(recommendationoptions_2_projectedutilizationmetrics_cpu_maximum, 'na'), ';',
        COALESCE(recommendationoptions_2_projectedutilizationmetrics_memory_maximum, 'na'), ';'
   ) option_details
   , tags as tags
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
        COALESCE(recommendationoptions_3_performancerisk, 'na'), ';',
        COALESCE(recommendationoptions_3_instancetype, 'na'), ';',
        COALESCE(recommendationoptions_3_migrationeffort, 'na'), ';',
        COALESCE(recommendationoptions_3_memory, 'na'), ';',
        COALESCE(recommendationoptions_3_vcpus, 'na'), ';',
        COALESCE(recommendationoptions_3_network, 'na'), ';',
        COALESCE(recommendationoptions_3_storage, 'na'), ';',
        CONCAT(
           (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_isarchitecturedifferent, 'na') = 'true') THEN 'Architecture ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_ishypervisordifferent, 'na') = 'true') THEN 'Hypervisor ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_isinstancestoreavailabilitydifferent, 'na') = 'true') THEN 'InstanceStoreAvailability ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_isnetworkinterfacedifferent, 'na') = 'true') THEN 'NetworkInterface ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_isstorageinterfacedifferent, 'na') = 'true') THEN 'StorageInterface ' ELSE '' END),
           (CASE WHEN (COALESCE(recommendationoptions_3_platformdifferences_isvirtualizationtypedifferent, 'na') = 'true') THEN 'VirtualizationType ' ELSE '' END)
        ), ';',
        COALESCE(recommendationoptions_3_projectedutilizationmetrics_cpu_maximum, 'na'), ';',
        COALESCE(recommendationoptions_3_projectedutilizationmetrics_memory_maximum, 'na'), ';'
   ) option_details
   , tags tags
   FROM
     compute_optimizer_ec2_instance_lines
   WHERE (instancearn LIKE '%arn:%')
     AND recommendationoptions_3_estimatedmonthlysavings_currency <> ''

)
