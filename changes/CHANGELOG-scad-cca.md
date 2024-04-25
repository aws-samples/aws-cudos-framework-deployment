# What's new in SCAD Containers Cost Allocation Dashboard
## SCAD Containers Cost Allocation Dashboard - v1.0.0
* Added support to view Net Amortized Cost in "View Cost As" control in all sheets
* Removed "Exlucde last 1 month" from all date range controls to prevent "No Data" (beacuse Split Cost Allocation Data for EKS starts filling data only in current month)
* Fixed issue where all split cost and usage metrics were lower than they should be, for pods on EC2 instances that were running for less than a full hour
* Fixed aggregation issues for usage metrics in Athena views

## SCAD Containers Cost Allocation Dashboard - v0.0.1
* Initial release
