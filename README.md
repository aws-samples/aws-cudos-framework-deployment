# Cloud Intelligence Dashboards (CUDOS Framework)

[![PyPI version](https://badge.fury.io/py/cid-cmd.svg)](https://badge.fury.io/py/cid-cmd)

## Welcome to Cloud Intelligence Dashboards (CUDOS Framework) automation repository

### The scripts in this repo have been succesfully tested in [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home) (`recommended`)

## Supported dashboards
- [CUDOS Dashboard](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed?dashboard=cudos)
- [Cost Intelligence Dashboard](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed?dashboard=cost_intelligence_dashboard)
- [Trusted Advisor Organisation (TAO) Dashboard](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed?dashboard=e1799d0d-166c-4e61-8fa6-5c927f70c799)
- [Trends Dashboard](https://d1s0yx3p3y3rah.cloudfront.net/anonymous-embed?dashboard=tao-dashboard?dashboard=trends-dashboard)

:white_check_mark: means that the step you are reading below *Is* compatible with a deployment of the dashboards that used the [Cloudformation deployment method](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/2b_cudos_dashboard/#option-3-cloudformation-deployment)

:heavy_exclamation_mark: means that the step you are reading *Is not* compatible with a deployment of the dashboards that used the [legacy automation](./legacy)

## Before you start
1. :heavy_exclamation_mark: Complete the prerequisites for respective dashboard
    - [CUDOS Dashboard](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/1_prerequistes/)
    - [Cost Intelligence Dashboard](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/cost-usage-report-dashboards/dashboards/1_prerequistes/)
    - [Trusted Advisor (TAO) Dashboard](https://tao.workshop.aws/prerequisites.html)
    - [Trends Dashboard](https://wellarchitectedlabs.com/cost/200_labs/200_cloud_intelligence/trusted-advisor-dashboards/dashboards/1_prerequistes/)

2. :heavy_exclamation_mark: [Specifying a Query Result Location Using a Workgroup](https://docs.aws.amazon.com/athena/latest/ug/querying.html#query-results-specify-location-workgroup)

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

5. List of supported commands  
    ```bash
    cid-cmd --help
    ```
6. Deploy a dashbaord  
    ```bash
    cid-cmd deploy
    ```
7. Update a dashbaord  
    ```bash
    cid-cmd update
    ```

### Example output

<pre>CLOUD INTELLIGENCE DASHBOARDS (CID) aka Cid CLI 1.0 Beta

Loading plugins...
  Core loaded
done

Usage: cid-cmd [OPTIONS] COMMAND [ARGS]...

Options:
  --profile_name TEXT           AWS Profile name to use
  --region_name TEXT            AWS Region (default:'us-east-1')
  --aws_access_key_id TEXT
  --aws_secret_access_key TEXT
  --aws_session_token TEXT
  -v, --verbose
  --help                        Show this message and exit.

Commands:
  delete  Delete Dashboard
  deploy  Deploy Dashboard
  map     Create account mapping
  open    Open Dashboard in browser
  status  Show Dashboard status
  update  Update Dashboard
</pre>


## Legacy (bash) automation has been moved under [**legacy**](./legacy/) directory
