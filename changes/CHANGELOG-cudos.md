# What's new in CUDOS Dashboard

## CUDOS - 4.75

* Databases: Added 'Daily Storage Cost' visual which shows detailed storage cost breakdown and can be used to track GP3 volumes adoption for Amazon RDS and OpenSearch 
* MoM Trends: Added Payer Account to 'AWS Marketplace spend detailed view'
* Data Transfer Summary: New visual 'Single-AZ VPC endpoints' which helps to asses reliability risks and consider to deploy production VPC endpoints in a several Availability Zones
* Data Transfer Summary: Data Transfer types categorization logic so you have more precise breakdown of different data transfer types


## CUDOS - 4.74

* MoM Trends: Added AWS Marketplace section with visuals 'AWS Marketplace spend by Legal Entity' and 'AWS Marketplace spend detailed view'
* MoM Trends: Added Control to filter by Legal Entity
* Monitoring and Observability: Merged visuals 'TOP 10 CloudWatch Resources Previous Month' and 'TOP 10 CloudWatch Log Resources Previous Month' into 'TOP 10 CloudWatch Resources' and changed time interval to last 30 days
* Monitoring and Observability: Added 'TOP 10 CloudWatch Resources Daily Cost' visual
* OPTICS Explorer: Added ability to filter by 'Billing Entity' and 'Legal Entity'
* Data Transfer Summary: S3 Transfer Acceleration added to Region to Internet data transfer type


## CUDOS - 4.73

* Compute Summary: 'Unused On-Demand Capacity Reservations Cost per Account' changed from monthly to daily aggregation for more granular visibility 
* Billing Summary: Drill down to description on 'Discounts: Credits, Refunds, Others' now grouped by discount type 
* End User Computing: Adjusted 'Cost Optimizer for Amazon WorkSpaces' solution name in Recommendations section

## CUDOS - 4.72

* Databases: Added ability to vizualise spend and usage for Amazon Neptune
* Compute Summary: Added insights and recommendations to AWS Lambda Summary section with the links to respective documentation
* RI/SP Summary: Added Cost line to ‘Avg. Hourly EC2 Cost by Pricing Model’ which allows to get total EC2 compute cost per hour


## CUDOS - 4.71

* Compute Summary: Changed  'On-Demand Capacity Reservations Usage Hours' visual to show data for Last 30 days instead of previous month so it displays current inventory and utilization of On-Demand Capacity Reservations
* Monitoring and Observability: Added CloudWatch Synthetics and CloudWatch Metrics Steams to 'CloudWatch Usage Cost per Usage Type Group' visual
* Monitoring and Observability: Added pricing unit and usage amount to 'TOP 10 CloudWatch Resources Previous Month' and 'TOP 10 CloudWatch Log Resources Previous Month' visuals


## CUDOS - 4.70

* Compute Summary: Added visuals 'Unused On-Demand Capacity Reservations Cost per Account' and 'On-Demand Capacity Reservations Usage Hours (Previous Month)'
* Compute Summary: Combined visuals 'EC2 Instance Type Running Hours Cost' and 'EC2 Family Running Hours Cost' into 'EC2 Running Hours Cost by Purchase Option' and added ability to switch between Instance Family and Instance Type with 'Group By' control 
* Compute Summary: Top 3 previous generation instances types Focus Area extended to top 5 added ability to switch between Instance Family and Instance Type with 'Group By' control 

## CUDOS - 4.69.1

* End User Computing: Added detailed description for Storage and Application Bundles in 'Workspaces spend per Bundle' and 'WorkSpaces Cost and Usage Top 20' vizuals

## CUDOS - 4.69

* Compute Summary: Added ability to choose service (ECS or EKS) for AWS Fargate visuals
* Compute Summary: 'TOP 20 Fargate Clusters' visual renamed to 'TOP 20 "ECS Fargate", "EKS Fargate" and "EKS Control Plane" cost' and shows corresponding Fargate and EKS Cluster Control plane charges
* End User Computing: Added 'Workspaces Count per Running Mode', 'Average Cost per WorkSpace','Average Usage for AutoStop WorkSpaces (hours)','Workspaces Count per Region','Workspaces spend per Bundle' and 'Average WorkSpaces cost per Region' visuals
* End User Computing: Added Bundle description to 'WorkSpaces Cost and Usage Top 20' and 'Workspaces AutoStop with monthly usage over 80 hours' visuals


## CUDOS - 4.68.1

* RI/SP Summary: Fix filters for "Amortised Spend by Purchase Option and Savings (Potential Savings Eligible Workloads Only)" vizual to exclude services which can't be covered by RIs or SPs 

## CUDOS - 4.68

* Databases: Replaced "Database Instance Daily Elasticity by Purchase Option" with "Database Instance Hours Daily Elasticity by Purchase Option" and added a unit metric to the visual 

## CUDOS - 4.67.3

* MoM Trends: Updated charge_type filter

## CUDOS - 4.67.2 

* Storage Summary: Filters applied to daily visuals changed to last 90 days fron last 3 months
* Payer and Account Name/ID controls now show only relevant values for respective control
* OPTICS Explorer: Relative dates filter instead of Start/End dates

## CUDOS - 4.67.1 

* Amazon S3: Minor calculation accuracy fix for "TOP 5 Accounts for Glacier Vault migration to Glacier Deep Archive Savings Opportunity" via "S3 Glacier Deep Archive Estimated Cost" calculated field

## CUDOS - 4.67

* Monitoring and Observability: New visual "TOP 10 CloudWatch Log Resources Previous Month"; Various improvements to actions on cloudwatch visuals; removed Operation from "TOP 10 CloudWatch Resources Previous Month" visual

## CUDOS - 4.66.3

* Monitoring and Observability: New recommendations

## CUDOS - 4.66.1

* MoM Trends: Removed billing entity field from visual "MoM Trends by Product Code (AWS Marketplace items use product_name)", control left as is

## CUDOS - 4.66

* MoM Trends: Additional visibility and control in to billing entity origin AWS vs AWS Marketplace

## CUDOS - 4.65

* Data Transfer: Amazon CloudFront is now a separate Data Transfer Type category; New multi-select list for Data Transfer Types

## CUDOS - 4.64.2

* MoM Trends: Updated filters on all MoM trends visuals to match edge cases for Refunds and Credits 

## CUDOS - 4.64.1

* Databases: Updated filters on all Database visuals to match edge cases for Refunds and Credits 

## CUDOS - 4.64

* Compute Summary: Excluded charges for Dedicated Hosts from EC2 instance family and instance types visuals
* Compute Summary: New visual ‘EC2 Spot Savings’
* End User Computing: Updated recommendations for Workspaces Cost Optimizer solution new capability to delete unused workspaces which will reduce costs for customers by terminating the workspaces which have not been used for a month

## CUDOS - 4.63.4

* Databases: Fixed a filter on "Database Instance Daily Elasticity by Purchase Option" to include OpenSearch Instances

## CUDOS - 4.63.3

* GameTech: Renamed "GameLift OnDemand Instance Types"(Monthly) to GameLift Costs by Instance Types; renamed "GameLift OnDemand Instance Types"(Daily) to "GameLift Instance Types Last 90 Days" and adjusted filters

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
