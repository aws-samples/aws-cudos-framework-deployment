# Cloud Intelligence Dashboards (CUDOS Framework)

[![PyPI version](https://badge.fury.io/py/cid-cmd.svg)](https://badge.fury.io/py/cid-cmd)


## Table of Contents
1. [Overview](#Overview)
1. [Architecture of Foundational Dashboards](#Architecture-of-Foundational-Dashboards)
1. [Cost](#Cost)
1. [Prerequisites](#Prerequisites)
1. [Deployment Steps](#Deployment-Steps)
1. [Cleanup](#Cleanup)
1. [FAQ](#FAQ)
1. [Changelogs](#Changelogs)
1. [Feedback](#Feedback)
1. [Notices](#Notices)


## Overview
The Cloud Intelligence Dashboards is an open-source framework, lovingly cultivated and maintained by a group of customer-obsessed AWSers, that gives customers the power to get high-level and granular insight into their cost and usage data. Supported by the Well-Architected framework, the dashboards can be deployed by any customer using a CloudFormation template or a command-line tool in their environment in under 30 minutes. These dashboards help you to drive financial accountability, optimize cost, track usage goals, implement best-practices for governance, and achieve operational excellence across all your organization.

Cloud Intelligence Dashboards Framework provides AWS customers with [more then 20 Dashboards](https://catalog.workshops.aws/awscid/dashboards/).
* Foundational Dashboards - A set of main Dashboards that only require Cost and Usage Report(CUR)
* Advanced Dashboards - Require CID Data Collection and CUR
* Additional Dashboards - Require various custom datasources or created for very specific use cases.

## Architecture of Foundational Dashboards

![Foundational Architecture](assets/images/foundational-architecture.png  "Foundational")

1. AWS Data Exports delivers daily the Cost & Usage Report (CUR2) to an Amazon S3 Bucket in the Management Account.
2. Amazon S3 replication rule copies Export data to a dedicated Data Collection Account S3 bucket automatically.
3. Amazon Athena allows querying data directly from the S3 bucket using an AWS Glue table schema definition.
4. Amazon QuickSight creates datasets from Amazon Athena , refreshes daily and caches in SPICE(Super-fast, Parallel, In-memory Calculation Engine) for Amazon QuickSight
5. User Teams (Executives, FinOps, Engineers) can access Cloud Intelligence Dashboards in Amazon QuickSight. Access is secured through AWS IAM, IIC (SSO), and optional Row Level Security.


## Cost
The following table provides a sample cost breakdown for deploying of Foundational Dashboards with the default parameters in the US East (N. Virginia) Region for one month. 

| AWS Service                     | Dimensions                    |  Cost [USD]      |
|---------------------------------|-------------------------------|------------------|
| S3 (CUR Storage)                | Monthly storage               | $5-10/month*     |
| AWS Glue Crawler                | Monthly operation.            | $3/month*        |
| AWS Athena                      | Data scanned monthly          | $15/month*       |
| QuickSight Enterprise (Authors) | 3 authors  ($24/month/author) | $72/month**      |
| QuickSight Enterprise (Readers) | 15 readers ($3/month/reader)  | $45/month**      |
| QuickSight SPICE Capacity       | 100 GB                        | $10-20/month*    |
| **Total Estimated Monthly Cost** |                              | **$100-$200**    |

\* Costs are relative to the size of your Cost and Usage Report (CUR) data  
\** Costs are relative to number of Users

**Additional Notes:**
- Free trial available for 30 days for 4 QuickSight users
- Actual costs may vary based on specific usage and data volume

Pleas use AWS Pricing Calculator for precise estimation.

## Prerequisites
You need access to AWS Accounts. We recommend deployment of the Dashboards in a dedicated Data Collection Account, other than your Management (Payer) Account. We provide provides a CloudFormation templates to copy CUR 2.0 data from your Management Account to a dedicated one. You can use it to aggregate data from multiple Management (Payer) Accounts or multiple Linked Accounts.

If you do not have access to the Management/Payer Account, you can still collect the data across multiple Linked accounts using the same approach.

The ownership of CID is usually with the FinOps team, who do not have administrative access. However, they require specific privileges to install and operate CID dashboards. To assist the Admin team in granting the necessary privileges to the CID owners, a CFN template is provided. This template, located at [CFN template](cfn-templates/cid-admin-policies.yaml), takes an IAM role name as a parameter and adds the required policies to the role.


## Deployment Steps
There are several ways we can deploy dashboards:
1. Using cid-cmd tool from command line
1. [CloudFormation Template](./cfn-templates/cid-cfn.yml) using cid-cmd tool in Amazon Lambda. (Recommended)

Please refer to the deployment documentation [here](https://catalog.workshops.aws/awscid/en-US/dashboards/foundational/cudos-cid-kpi/deploy).

## Cleanup
Please refer to the documentation [here](https://catalog.workshops.aws/awscid/en-US/dashboards/teardown).

## FAQ
Please refer to the documentation [here](https://catalog.workshops.aws/awscid/en-US/faqs).

## Changelogs
For dashboards please check Change Logs [here](changes/)
For CID deployment tool, including Cli and CFN please check [Releases](/releases)

## Feedback
Please reference to [this page](https://catalog.workshops.aws/awscid/en-US/feedback-support)


## Notices
Dashboards and their content: (a) are for informational purposes only, (b) represents current AWS product offerings and practices, which are subject to change without notice, and (c) does not create any commitments or assurances from AWS and its affiliates, suppliers or licensors. AWS content, products or services are provided “as is” without warranties, representations, or conditions of any kind, whether express or implied. The responsibilities and liabilities of AWS to its customers are controlled by AWS agreements, and this document is not part of, nor does it modify, any agreement between AWS and its customers.