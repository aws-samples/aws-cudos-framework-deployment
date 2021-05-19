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

8. Run the ./shell-script/customer-cudos.sh script from the **cudos** directory (NOT from cudos/shell-script)

  *Note: Your user would require minimal permissions on the IAM Role described in  [minimal_permissions.json](https://github.com/aws-samples/aws-cudos-framework-deployment/blob/main/cudos/minimal_permissions.json)*

  *Note: `map` parameter requires AWS Organisations API [ListAccounts](https://docs.aws.amazon.com/organizations/latest/APIReference/API_ListAccounts.html)*

  **Important: Run each of these one at a time in the order they appear below**

  ```bash
  ./shell-script/customer-cudos.sh config
  ./shell-script/customer-cudos.sh prepare
  ./shell-script/customer-cudos.sh deploy-datasets
  ./shell-script/customer-cudos.sh deploy-dashboard
  ./shell-script/customer-cudos.sh deploy-cid-dashboard
  ./shell-script/customer-cudos.sh map
  ./shell-script/customer-cudos.sh refresh-data-sets
  ```

9. Set up [scheduled SPICE refresh](https://docs.aws.amazon.com/quicksight/latest/user/refreshing-imported-data.html#schedule-data-refresh) for the SPICE datasets:
    - summary_view
    - ec2_running_cost
    - compute_savings_plan_eligible_spend
    - s3_view

10. To pull updates run

    ```bash
    ./shell-script/customer-cudos.sh update-dashboard
    ```

11. To delete CUDOS dashboard and datasets from Amazon QuickSight run

    ```bash
    ./shell-script/customer-cudos.sh delete
    ./shell-script/customer-cudos.sh cleanup
    ```

12. To delete CID dashboard from Amazon QuickSight run

    ```bash
    ./shell-script/customer-cudos.sh cid-delete
    ```
