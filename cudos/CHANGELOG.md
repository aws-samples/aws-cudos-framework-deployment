# What's new in CUDOS Dashboard

## CUDOS - 4.56.1

* RI/SP Summary: New recommendation on Budgets
* MoM Trends: New recommendation on AWS Cost Anomaly Detection
* Storage Sumary: Renamed "TOP EBS Spend Accounts Previous Month" to "TOP EBS Spend Accounts Last 3 Months"

## CUDOS - 4.56

* Compute/Media/Message Brokers: TOP Visuals for Lambda, Fargate Clusters, Kinesis, Elemental now have 20 and 5 distinct filters delivering better granularity in visualisation, and visualise last 30 days
* DynamoDB: TOP 15 Dynamo DB Tables Previous Month Usage Cost now visualises last 30 days, added account what the table belongs to and now has an action filter to Daily Cost per Table Previous Month
* DynamoDB: DynamoDB Period over period was missing a charge_type filter, fixed

## CUDOS - 4.55
* Data Transfer now includes only chargable DTO. Example: Excluding S3, ALB -> CloudFront, as it is not charged.

## CUDOS - 4.54
* Scale optimised for smaller screens

## CUDOS - 4.53.2
* S3: Daily Storage Bucket Explorer now visualises total bucket usage amount

## CUDOS - 4.53
* DynamoDB: Cost breakdown per account is now visualised in categories, OnDemand = PayPerRequest, Commited Throughput is CommitedThroughput that is not covered by Reservations

## CUDOS - 4.52
* Billing Summary: Discounts now show positive value; New visual showing discounts and their type MoM

## CUDOS - 4.51.2
* Storage Summary: Fixed a type on the EBS Explorer filter

## CUDOS - 4.51.1
* RI/SP Summary: Removed a filter on a few visuals that was breaking on filtering by account ids

## CUDOS - 4.51
* AI/ML: Textract and Rekognition visuals

## CUDOS - 4.50.1
* AI/ML: SageMaker Savings Plan recommendations

## CUDOS - 4.50
* Compute Summary: EC2 Running Hours by Platform Last 3 Month introducing OS details
* Compute Summary: TOP 20 Lambdas Previous Month Account in Tooltip

## CUDOS - 4.49
* Compute Summary: Renamed “EC2 Coverage MoM (Cost)” to EC2 Running Hours Cost by Purchase Option
* Storage Summary: TOP 20 EBS Volumes Previous Month EBS Volumes and Snapshots have dedicated visuals
* Data Transfer: VPC Endpoint Utilisation
* S3: Top 10 Buckets MoM now uses single visual
* GameTech and Media: Elemental MediaConvert Elasticity by purchase option

## CUDOS - 4.48.3
* Message Brokers: Kinesis best practice recommendations
* Databases: *6g instance type migration considerations
* GameTech & Media: +Tooltip over TOP 20 resource IDs

## CUDOS - 4.48
* Message Brokers: +Amazon MSK Visuals

## CUDOS - 4.47.1
* Billing Summary: TOP 10 accounts spend now includes Marketplace charges
