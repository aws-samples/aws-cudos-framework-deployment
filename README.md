# Cloud Intelligence Dashboards (CUDOS Framework)

[![PyPI version](https://badge.fury.io/py/cid-cmd.svg)](https://badge.fury.io/py/cid-cmd)

## Welcome to Cloud Intelligence Dashboards (CUDOS Framework) automation repository
This repository contains CloudFormation templates, Terraform modules, and a Command Line tool (cid-cmd) for managing various dashboards provided in AWS Well Architected LAB [Cloud Intelligence Dashboards](https://www.wellarchitectedlabs.com/cloud-intelligence-dashboards/).

There are several ways we can manage dashboards:
1. [CloudFormation Template](./cfn-templates/cid-cfn.yml) (using cid-cmd tool in lambda)
2. [Terraform module](./terraform-modules/cid-dashboards/README.md) (wrapper around CloudFormation Template)
3. Using cid-cmd tool from command line

We recommend cid-cmd tool via [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home).

## Supported dashboards
---
| Dashboard documentation | Demo URL | Prerequisites URL |
| --- | --- | --- |
| [CUDOS Dashboard](https://catalog.workshops.aws/awscid/en-US/dashboards/foundational/cudos-cid-kpi#cudos-dashboard) | [demo](https://cid.workshops.aws.dev/demo?dashboard=cudos) | [link](https://aws.amazon.com/aws-cost-management/aws-cost-and-usage-reporting) |
| [Cost Intelligence Dashboard](https://catalog.workshops.aws/awscid/en-US/dashboards/foundational/cudos-cid-kpi#cost-intelligence-dashboard-(cid)) | [demo](https://cid.workshops.aws.dev/demo?dashboard=cost_intelligence_dashboard) | [link](https://aws.amazon.com/aws-cost-management/aws-cost-and-usage-reporting) |
| [Trusted Advisor Organisation (TAO) Dashboard](https://catalog.workshops.aws/awscid/en-US/dashboards/advanced/trusted-advisor) | [demo](https://cid.workshops.aws.dev/demo?dashboard=tao-dashboard) | [link](https://catalog.workshops.aws/awscid/en-US/dashboards/advanced/trusted-advisor/prerequisites) |
| [Trends Dashboard](https://catalog.workshops.aws/awscid/en-US/dashboards/additional/trends) | [demo](https://cid.workshops.aws.dev/demo?dashboard=trends-dashboard) | [link](https://aws.amazon.com/aws-cost-management/aws-cost-and-usage-reporting) |
| [KPI Dashboard](https://catalog.workshops.aws/awscid/en-US/dashboards/foundational/cudos-cid-kpi#kpi-dashboard) | [demo](https://cid.workshops.aws.dev/demo?dashboard=kpi) | [link](https://aws.amazon.com/aws-cost-management/aws-cost-and-usage-reporting) |
| [Compute Optimizer Dashboard](https://catalog.workshops.aws/awscid/en-US/dashboards/advanced/compute-optimizer) | [demo](https://cid.workshops.aws.dev/demo?dashboard=compute-optimizer-dashboard) | [link](https://catalog.workshops.aws/awscid/en-US/dashboards/advanced/compute-optimizer/prerequisites) |
| [Cost Anomaly Dashboard](https://catalog.workshops.aws/awscid/en-US/dashboards/advanced/cost-anomaly) | [demo](https://cid.workshops.aws.dev/demo?dashboard=aws-cost-anomalies) | [link](https://catalog.workshops.aws/awscid/en-US/dashboards/advanced/cost-anomaly/prerequisites) |
| [Data Transfer Cost Dashboard](https://catalog.workshops.aws/awscid/en-US/dashboards/additional/data-transfer) | [demo](https://cid.workshops.aws.dev/demo?dashboard=datatransfer-cost-analysis-dashboard) | [link](https://catalog.workshops.aws/awscid/en-US/dashboards/foundational/cudos-cid-kpi) |

See more dashboards on the [workshop page](https://catalog.workshops.aws/awscid/en-US/dashboards).

## Before you start
1. :heavy_exclamation_mark: Complete the prerequisites for respective dashboard (see above).
2. :heavy_exclamation_mark: [Specifying a Query Result Location Using a Workgroup](https://docs.aws.amazon.com/athena/latest/ug/querying.html#query-results-specify-location-workgroup)
3. :heavy_exclamation_mark: Make sure QuickSight [Enterprise edition](https://aws.amazon.com/premiumsupport/knowledge-center/quicksight-enterprise-account/) is activated.

## Command line tool cid-cmd

#### Demo: Deployment of Dashboards with cid-cmd tool

   [![asciicast](https://asciinema.org/a/467770.svg)](https://asciinema.org/a/467770)

#### Install

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

#### Dasbhoard Deployment

```bash
cid-cmd deploy
```


#### Update existing Dashboards
Update only Dashboard
```bash
cid-cmd update
```
Update dashboard and all dependenies (Datasets and Athena View). WARNING: this will overide any customization of SQL files and Datasets.
```bash
cid-cmd update --force --recursive
```
#### Show Dashboard status
Show dashboards status

```bash
cid-cmd status
```

####  Share QuickSight resources
```bash
cid-cmd share
```

#### Initialize Amazon QuickSight
One time action to intialize Amazon QuickSight Enerprise Edition.

```bash
cid-cmd initqs
```


#### Delete Dashboard and all dependencies unused by other
Delete Dashboards and all dependencies unused by other CID-managed dashboards.(including QuickSight datasets, Athena views and tables)
```bash
cid-cmd delete
```
#### Delete Command Options:
```
 --dashboard-id TEXT QuickSight dashboard id 
 --athena-database TEXT Athena database
 ```

#### Export
The command `export` lets you download or share a customized dashboard with another AWS Account. It takes the QuickSight Analysis as an input and generates all the assets needed to deploy your Analysis into another AWS Account. This command will generate a yaml file with a description of the Dashboard and all required Datasets. Also this command generates a QuickSight Template in the current AWS Account that can be used for Dashboard deployment in other accounts. The resource file can be used with all other cid commands. Both accounts must have relevant Athena Views and Tables.

Export from account A:
```
cid-cmd export
```

Deployment to account B:
```
cid-cmd deploy --resources ./mydashboard.yaml
```

#### See available commands and command line options
```
cid-cmd --help
```

#### CSV to Athena View
Generate and SQL file for Athena View for CSV file

```
cid-cmd csv2view --input my_mapping.csv --name my_mapping
```
This command generates a SQL file that you can execute. Please mind [Athena Service Limit for Query Size](https://docs.aws.amazon.com/athena/latest/ug/service-limits.html#service-limits-query-string-length).


## Cloud Formation
CID is also provided in a form of CloudFormation telmplates. See detailed instuctions in the [Well Architected Labs](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/deploy_dashboards/) site.

## Terraform
CID offers a set of Terraform modules to deploy CUR replicaion and CID dashboards. These modules act as a wrapper around CloudFormation.

  1. Create a bucket for consolidating CUR [terraform-modules/cur-setup-destination/](terraform-modules/cur-setup-destination/)
  2. Create a CUR in Payer Account(s) [terraform-modules/cur-setup-source/](terraform-modules/cur-setup-source/)
  3. Create Dashboards [terraform-modules/cid-dashboards/](terraform-modules/cid-dashboards/)


## Rights Management
The ownership of CID is usually with the FinOps team, who do not have administrative access. However, they require specific privileges to install and operate CID dashboards. To assist the Admin team in granting the necessary privileges to the CID owners, a CFN template is provided. This template, located at [CFN template](cfn-templates/cid-admin-policies.yaml), takes an IAM role name as a parameter and adds the required policies to the role.


## Troubleshooting and Support
If you experience unexpected behaviour of the `cid-cmd` script please run `cid-cmd` in debug mode:

```bash
cid-cmd -vv [command]
```
    
This will produce a log file in the same directory that were at the tile of launch of cid-cmd. 

:heavy_exclamation_mark:Inspect the produced debug log for any sensitive information and anonymize it.

We encourage you to open [new issue](https://github.com/aws-samples/aws-cudos-framework-deployment/issues/new) with description of the problem and attached debug log file.
