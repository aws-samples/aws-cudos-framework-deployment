# Pre-Requisites

1. Enable [Trusted Advisor Organizational View](https://docs.aws.amazon.com/awssupport/latest/user/organizational-view.html#enable-organizational-view)

2. Create Trusted Advisor Organizational View [report](https://docs.aws.amazon.com/awssupport/latest/user/organizational-view.html#create-organizational-view-reports). Select **JSON** format for the report.

3. Download Trusted Advisor Organizational View [report](https://docs.aws.amazon.com/awssupport/latest/user/organizational-view.html#download-organizational-view-reports) and unzip it

4. Create S3 bucket. Create prefix (folder) called reports

5. Upload report unzipped folder from step 3 to s3://{bucket}/reports

6. Subscribe to [Amazon QuickSight Enterprise Edition](https://docs.aws.amazon.com/quicksight/latest/user/signing-up.html)

7. Grant access for Amazon QuickSight service to [S3 bucket](https://docs.aws.amazon.com/quicksight/latest/user/accessing-data-sources.html)
    - Open Manage QuickSight
    - In Security & Permissions section click *Add or remove* under QuickSight access to AWS services
    - Tick check box for Amazon Athena
    - Tick check box for s3 bucket created in step 4

# Deployment

1. Launch [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home) and Run the following script: 
    
    Note: Your user would require minimal permissions on the IAM Role described in  minimal_permissions.json
    ```bash
    ./shell-script/tao.sh --action=prepare
    ```
    ```bash
    ./shell-script/tao.sh --action=deploy
    ```
2. To refresh **AWS Trusted Advisor Organizational View** data (we recommend to perform this step at least once per month):
    - Create AWS Trusted Advisor Organizational View [report](https://docs.aws.amazon.com/awssupport/latest/user/organizational-view.html#create-organizational-view-reports)
    - Download AWS Trusted Advisor Organizational View [report](https://docs.aws.amazon.com/awssupport/latest/user/organizational-view.html#download-organizational-view-reports) and unzip it
    - Upload report unzipped folder to s3://{bucket}/reports
    - Run following script: 

        ```bash
        ./shell-script/tao.sh --action=refresh-data
        ```
# Update

1. To pull dashboard updates run

    ```bash
    ./shell-script/tao.sh --action=update
    ```

# Cleanup

1. To delete TAO dashboard and datasets from QuickSight run

    ```bash
    ./shell-script/tao.sh --action=delete
    ```
