# What's new in SCAD Containers Cost Allocation Dashboard

## SCAD Containers Cost Allocation Dashboard - v2.0.0
* Added support for AWS Split Cost Allocation Data (SCAD) for ECS:
  * All visuals now include SCAD ECS data (including AWS Batch on ECS), in addition to SCAD EKS data
  * The "EKS Breakdown" sheet has been renamed "Cluster Breakdown"
* CUR 2.0 support: The dashboard now defaults to CUR 2.0, and still supports legacy CUR
* The `scad_cca_summary_view` and `scad_cca_hourly_resource_view` Athena views have been converged to a single view.  
The time and data granularity levels remain the same, but now in a single view instead of 2 views
* The hourly and resource-level interactive visuals in the "Cluster Breakdown" sheet have been removed, and converged with the visuals in the "Workloads Explorer" tab, which now have hourly and resource-level data, in addition to the current granularity levels in these visuals

Note:
Starting this version (v2.0.0), the `scad_cca_hourly_resource_view` QuickSight dataset and Athena view are no longer used by the dashboard.
Following an upgrade to this version (v2.0.0), after verifying functionality of the dashboard, you can delete the `scad_cca_hourly_resource_view` QuickSight dataset and Athena view (in this order).
They won't be deleted automatically, and will continue refreshing and incurring cost if you don't delete them.
Deleting the `scad_cca_hourly_resource_view` QuickSight dataset and Athena view is not necessary on a new installation of the dashboard, only following an upgrade.
Deleteing a QuickSight dataset: https://docs.aws.amazon.com/quicksight/latest/user/delete-a-data-set.html
Deleting an Athena view: https://docs.aws.amazon.com/athena/latest/ug/drop-view.html

## SCAD Containers Cost Allocation Dashboard - v1.0.0
* Added support to view Net Amortized Cost in "View Cost As" control in all sheets
* Removed "Exlucde last 1 month" from all date range controls to prevent "No Data" (beacuse Split Cost Allocation Data for EKS starts filling data only in current month)
* Fixed issue where all split cost and usage metrics were lower than they should be, for pods on EC2 instances that were running for less than a full hour
* Fixed aggregation issues for usage metrics in Athena views

## SCAD Containers Cost Allocation Dashboard - v0.0.1
* Initial release
