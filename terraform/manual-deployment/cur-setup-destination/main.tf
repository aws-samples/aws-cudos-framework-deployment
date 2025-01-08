resource "aws_cloudformation_stack" "data_exports_child" {
  # checkov:skip=CKV_AWS_124:SNS topic not required for this use case
  provider     = aws
  name         = "data-exports-aggregation-child"
  template_url = "https://aws-managed-cost-intelligence-dashboards.s3.amazonaws.com/cfn/${var.global_values.tag_version}/data-exports-aggregation.yaml"
  capabilities = ["CAPABILITY_IAM", "CAPABILITY_NAMED_IAM"]
  parameters = {
    DestinationAccountId = var.global_values.destination_account_id
    ResourcePrefix       = var.data_exports_child.resource_prefix
    ManageCUR2           = var.data_exports_child.manage_cur2
    ManageFOCUS          = var.data_exports_child.manage_focus
    ManageCOH            = var.data_exports_child.manage_coh
    SourceAccountIds     = var.global_values.source_account_ids
    EnableSCAD           = var.data_exports_child.enable_scad
    RolePath             = var.data_exports_child.role_path
    TimeGranularity      = var.data_exports_child.time_granularity
  }
}