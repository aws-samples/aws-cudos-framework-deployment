# Pre-Requisites

*Note: If the customer has multiple payer accounts, this will need to be done for each payer account individually.*
 
1. Set up Hourly CUR with Athena compatibility and resource_ids and wait at least 24 hours. 

2. Deploy crawler-cfn.yml CloudFormation template generated in the CUR S3 bucket

3. Setup Amazon Athena "Query result location" in the Athena "primary" Workgroup

4. Subscribe to Amazon QuickSight Enterprise Edition.

5. Give Amazon QuickSight role access to CUR bucket

6. Purchase required amount of SPICE capacity for Amazon QuickSight

7. Launch a AWS CloudShell and upgrade the AWS CLI on your AWS CloudShell

  `curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"`

  `unzip awscliv2.zip`

  `sudo ./aws/install --update`

8. Run the ./shell-script/customer-cudos.sh script

  Note: Your user would require minimal permissions on the IAM Role described in  minimal_permissions.json

  `./shell-script/customer-cudos.sh config`

  `./shell-script/customer-cudos.sh prepare`

  `./shell-script/customer-cudos.sh deploy-datasets`

  `./shell-script/customer-cudos.sh deploy-dashboard`

  `./shell-script/customer-cudos.sh map`

  `./shell-script/customer-cudos.sh refresh-data-sets`

9. Set up automatic SPICE refresh for the SPICE datasets

10. To pull updates run

  `./shell-script/customer-cudos.sh update-dashboard`

11. To delete CUDOS dashboard and datasets from Amazon QuickSight run

  `./shell-script/customer-cudos.sh delete`

  `./shell-script/customer-cudos.sh cleanup`
