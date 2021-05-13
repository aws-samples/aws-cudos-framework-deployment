# Pre-Requisites

*Note: If the customer has multiple payer accounts, this will need to be done for each payer account individually.*

1. Set up Hourly CUR with Athena compatibility and resource_ids and wait at least 24 hours.

2. Deploy crawler-cfn.yml CloudFormation template generated in the CUR S3 bucket

3. [Setup Amazon Athena "Query result location" in the Athena "primary" Workgroup](https://docs.aws.amazon.com/athena/latest/ug/querying.html#query-results-specify-location-workgroup)

4. Subscribe to [Amazon QuickSight Enterprise Edition](https://docs.aws.amazon.com/quicksight/latest/user/signing-up.html)

5. Give Amazon QuickSight role access to CUR bucket

6. Purchase required amount of SPICE capacity for Amazon QuickSight

7. Launch [AWS CloudShell](https://console.aws.amazon.com/cloudshell/home) and [upgrade the AWS CLI on your AWS CloudShell](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2-linux.html)

  ```bash
  curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
  unzip awscliv2.zip
  sudo ./aws/install --update
  ```

8. Run the ./shell-script/trends.sh script from the **trends** directory (NOT from trends/shell-script)

  *Note: Your user would require minimal permissions on the IAM Role described in  [minimal_permissions.json](https://github.com/aws-samples/aws-cudos-framework-deployment/blob/main/cudos/minimal_permissions.json)*

  *Note: `map` parameter requires AWS Organisations API [ListAccounts](https://docs.aws.amazon.com/organizations/latest/APIReference/API_ListAccounts.html)*

  ```bash
  ./shell-script/trends.sh config
  ./shell-script/trends.sh prepare
  ./shell-script/trends.sh deploy-datasets
  ./shell-script/trends.sh deploy-dashboard
  ./shell-script/trends.sh map
  ./shell-script/trends.sh refresh-data-sets
  ```

9. Set up [scheduled SPICE refresh](https://docs.aws.amazon.com/quicksight/latest/user/refreshing-imported-data.html#schedule-data-refresh) for the SPICE datasets:
    - daily_anomaly_detection
    - monthly_anomaly_detection
    - monthly_bill_by_account

10. To pull updates run

    ```bash
    ./shell-script/trends.sh update-dashboard
    ```

11. To delete Trends dashboard, datasets from Amazon QuickSight and views from Athena run

    ```bash
    ./shell-script/trends.sh delete
    ./shell-script/trends.sh cleanup
    ```