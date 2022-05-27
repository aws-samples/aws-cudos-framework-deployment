# Cloud Intelligence Dashboards (CUDOS Framework)

[![PyPI version](https://badge.fury.io/py/cid-cmd.svg)](https://badge.fury.io/py/cid-cmd)

## Welcome to Cloud Intelligence Dashboards (CUDOS Framework) automation repository
This repository contains CloudFormation templates and Command Line tool (cid-cmd) for managing various dashboards provided in AWS Well Architected LAB [Cloud Intelligence Dashboards](https://www.wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/).

There are several ways we can manage dashboards:
1. Manual (2 hours) 
2. CloudFormation Tempalte (30 mins)
3. (`recommended`) Using cid-cmd tool. (5 mins) 

We recommend cid-cmd tool via [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home).

## Supported dashboards
---
| Dashboard documentation | Demo URL | Prerequisites URL |
| --- | --- | --- |
| [CUDOS Dashboard](https://www.wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/2b_cudos_dashboard/) | [demo](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed?dashboard=cudos) | [link](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/1_prerequistes/) |
| [Cost Intelligence Dashboard](https://www.wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/2a_cost_intelligence_dashboard/) | [demo](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed?dashboard=cost_intelligence_dashboard) | [link](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/1_prerequistes/) |
| [Trusted Advisor Organisation (TAO) Dashboard](https://www.wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/trusted-advisor-dashboards/) | [demo](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed?dashboard=e1799d0d-166c-4e61-8fa6-5c927f70c799) | [link](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/trusted-advisor-dashboards/dashboards/1_prerequistes/) |
| [Trends Dashboard](https://www.wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/3_additional_dashboards/#trends-dashboard) | [demo](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed?dashboard=trends-dashboard) | [link](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/1_prerequistes/) |
| [KPI Dashboard](https://www.wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/2c_kpi_dashboard/) | [demo](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed?dashboard=kpi) | [link](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/1_prerequistes/) |
| [Compute Optimizer Dashboard](https://www.wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/compute-optimizer-dashboards/) | [demo](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed?dashboard=compute-optimizer-dashboard) | [link](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/compute-optimizer-dashboards/dashboards/1_prerequisites/) |


## Before you start
1. :heavy_exclamation_mark: Complete the prerequisites for respective dashboard (see above).
2. :heavy_exclamation_mark: [Specifying a Query Result Location Using a Workgroup](https://docs.aws.amazon.com/athena/latest/ug/querying.html#query-results-specify-location-workgroup)
3. :heavy_exclamation_mark: Make sure QuickSight [Enterprise edition](https://aws.amazon.com/premiumsupport/knowledge-center/quicksight-enterprise-account/) is activated.

## How to use

1. Launch [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home) or your local shell

    Automation requires Python 3

2. Make sure you have latest pip package installed
    ```bash
    python3 -m ensurepip --upgrade
    ```

4. Install CID Python automation PyPI package
    ```bash
    pip3 install --upgrade cid-cmd
    ```

5. Deploy the Dashboards
    ```bash
    cid-cmd deploy
    ```
#### Optional Commands

6. Update existing Dashboards
    ```bash
    cid-cmd update
    ```

7. See available commands and command line options
    ```
    cid-cmd --help
    ```

### Usage Demo

   [![asciicast](https://asciinema.org/a/467770.svg)](https://asciinema.org/a/467770)

## Troubleshooting 

If you experience unexpected behaviour of the cid-cmd script please run cid-cmd in debug mode 

```bash
cid-cmd -vv [command]
```
    
This will produce a log file in the same directory that were at the tile of launch of cid-cmd. 

:heavy_exclamation_mark:Inspect the produced debug log for any sensitive information and anonimise it.

We encourage you to open [new issue](https://github.com/aws-samples/aws-cudos-framework-deployment/issues/new) with description of the problem and attached debug log file.
