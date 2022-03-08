# What's new in the KPI Dashboard

## KPI - 1.2
* Metrics Summary: Added EC2 Unit Cost to EC2 section
* KPI S3 Storage All Athena view: Updated product_volume_type case when statement to key off only '%Intelligent%' for Intelligent Tiering to meet AIA formatting

## KPI - 1.1
* Calculated field correction for Normalized Usage Quantity in the summary_view and kpi_instance_all data sets. 
    ```bash
    ifelse(
    locate({instance_type}, '10xlarge')>0, 80*{usage_quantity},
    locate({instance_type}, '12xlarge')>0, 96*{usage_quantity},
    locate({instance_type}, '16xlarge')>0, 128*{usage_quantity},
    locate({instance_type}, '18xlarge')>0, 144*{usage_quantity},
    locate({instance_type}, '24xlarge')>0, 192*{usage_quantity},
    locate({instance_type}, '32xlarge')>0, 256*{usage_quantity}, 
    locate({instance_type}, '2xlarge')>0, 16*{usage_quantity},
    locate({instance_type}, '4xlarge')>0, 32*{usage_quantity},
    locate({instance_type}, '8xlarge')>0, 64*{usage_quantity},
    locate({instance_type}, '9xlarge')>0, 72*{usage_quantity},
    locate({instance_type}, 'nano')>0, .25*{usage_quantity},
    locate({instance_type}, 'micro')>0, 0.5*{usage_quantity},
    locate({instance_type}, 'small')>0, 1*{usage_quantity},
    locate({instance_type}, 'medium')>0, 2*{usage_quantity},
    locate({instance_type}, 'xlarge')>0, 8*{usage_quantity},
    locate({instance_type}, 'large')>0, 4*{usage_quantity},
    {usage_quantity})
    ```

## KPI - 1
* Launch of KPI Dashboard
