resource "aws_cloudformation_stack" "data_exports_management" {
  # checkov:skip=CKV_AWS_124:SNS topic not required for this use case
  name         = "data-exports-aggregation-mgmt"
  provider     = aws
  template_url = "https://aws-managed-cost-intelligence-dashboards.s3.amazonaws.com/cfn/${var.global_values.tag_version}/data-exports-aggregation.yaml"
  capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
  parameters = {
    DestinationAccountId = var.global_values.destination_account_id
    ResourcePrefix       = var.data_exports_management.mgmt_resource_prefix
    ManageCUR2           = var.data_exports_management.mgmt_manage_cur2
    ManageFOCUS          = var.data_exports_management.mgmt_manage_focus
    ManageCOH            = var.data_exports_management.mgmt_manage_coh
    SourceAccountIds     = var.global_values.source_account_ids
    EnableSCAD           = var.data_exports_management.mgmt_enable_scad
    RolePath             = var.data_exports_management.mgmt_role_path
    TimeGranularity      = var.data_exports_management.mgmt_time_granularity
  }
}