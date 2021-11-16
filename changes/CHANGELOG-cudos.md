# What's new in CUDOS Dashboard

## CUDOS - 4.63.2

* DynamoDB: Including replication costs now in “TOP 15 Candidates for IA Tables Previous Month”

## CUDOS - 4.63.1

* DynamoDB: New visual “TOP 15 Candidates for IA Tables Previous Month”
* DynamoDB: Renamed “Ondemand” to “Commited Throughput” on “DynamoDB Provisioned Capacity Hourly Usage by Purchase Option Last 30 Days” visual

## CUDOS - 4.62

* DynamoDB: “Total Reservations Cost Previous Month” renamed to “Total Reservations Savings Previous Month” and now shows reservation type breakdown
* DynamoDB: New recommendations for IA Table Class
* DynamoDB: Renamed “DynamoDB MoM Unused Cost” to “DynamoDB MoM Reservations Unused Cost” and added additional controls for more fine grained visualisation

## CUDOS - 4.61.3

* Storage Summary: Renaming "EBS Unit Cost" to "EBS Storage Unit Cost"

## CUDOS - 4.61.2

* RI/SP Summary: "Savings Option for Compute by Owner / Consumer Previous Month" now applies "Amazon Elastic Container Service filter" 

## CUDOS - 4.61.1

* DynamoDB: Renamed Visual "DynamoDB PayPerRequestThroughput Usage and Cost Last 3 Months" to "DynamoDB PayPerRequestThroughput(OnDemand) Usage and Cost Last 90 Days" and reapplied filters
 
## CUDOS - 4.61

* S3: New visual TOP 5 Accounts for Glacier Vault migration to Glacier Deep Archive Savings Opportunity 

## CUDOS - 4.60.5

* Databases: Fixed daily filters to last 90 days and updated visual names. 

## CUDOS - 4.60.4

* About: Updated the About tab. 

## CUDOS - 4.60.3

* DataTransfer: Added classification "Other" for all unclassified datatransfer. 

## CUDOS - 4.60.2

* Compute: EC2 Family Running Hours Cost Last 90 Days visual now has a focus area controll on the right to filter in or out diferent purchase options

## CUDOS - 4.60.1

* MoM Trends: Aligned charge type filters on all visuals 

## CUDOS - 4.60

* Databases: Elasticsearch renamed to OpenSearch
* End User Computing: WorkSpaces Autostop visuals filter on the last 30 days now, instead of the previous month
* DataTransfer: Resource level visuals filter on the last 30 days now, instead of the previous month
* MoM Trends: Added MoM difference in absolute values (MoM $), now its possible to sort by all columns

## CUDOS - 4.59.1

* DynamoDB: PITR recommendation now has a link to the AWS documentation. 

## CUDOS - 4.59

* Compute Summary: New visual "TOP 10 Accounts by EC2 CPU Credit Usage Cost" and related recommendation. 

## CUDOS - 4.58

* RI/SP Summary: Renamed Previous Month Savings → Previous Month Net Savings; Renamed Usage Saving by Pricing Model and Service → Usage Net Saving by Pricing Model and Service; Now these two visuals show NET savings with respect to unutilized savings, this affects customers with unitilized ri/sp.

## CUDOS - 4.57

* Sheet Visit Anonymous Statistics. We added this little icon 📊 to each sheet to better prioritise new visuals and features for CUDOS Dashboard based on the sheet popularity. No PII data is collected, we are querying frequency of the icon download from the CloudFront logs of the CloudFront distribution where the icon is stored. If you would like to opt-out of this anonymous statistics collection, please save your dashboard as analysis and remove the icon from the text blocks 

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
