resource "aws_cloudformation_stack" "data_exports_child" {
  # checkov:skip=CKV_AWS_124:SNS topic not required for this use case
  provider     = aws.destination_account
  name         = "data-exports-aggregation-child"
  template_url = "https://aws-managed-cost-intelligence-dashboards.s3.amazonaws.com/cfn/data-exports-aggregation.yaml"
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


resource "aws_cloudformation_stack" "data_exports_management" {
  # checkov:skip=CKV_AWS_124:SNS topic not required for this use case
  depends_on = [
    aws_cloudformation_stack.data_exports_child
  ]
  name         = "data-exports-aggregation-mgmt"
  provider     = aws
  template_url = "https://aws-managed-cost-intelligence-dashboards.s3.amazonaws.com/cfn/data-exports-aggregation.yaml"
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


resource "aws_cloudformation_stack" "cudos_dashboard" {
  # checkov:skip=CKV_AWS_124:SNS topic not required for this use case
  name     = "cudos-dashboard-stack"
  provider = aws.destination_account
  depends_on = [
    aws_cloudformation_stack.data_exports_management,
    aws_cloudformation_stack.data_exports_child
  ]
  capabilities = ["CAPABILITY_NAMED_IAM", "CAPABILITY_IAM"]
  template_url = "https://aws-managed-cost-intelligence-dashboards.s3.amazonaws.com/cfn/cid-cfn.yml"
  parameters = {
    PrerequisitesQuickSight            = var.cudos_dashboard.prerequisites_quicksight
    PrerequisitesQuickSightPermissions = var.cudos_dashboard.prerequisites_quicksight_permissions
    QuickSightUser                     = var.global_values.quicksight_user
    LakeFormationEnabled               = var.cudos_dashboard.lake_formation_enabled

    # CUR Parameters
    CURVersion                      = var.cudos_dashboard.cur_version
    DeployCUDOSv5                   = var.cudos_dashboard.deploy_cudos_v5
    DeployCostIntelligenceDashboard = var.cudos_dashboard.deploy_cost_intelligence_dashboard
    DeployKPIDashboard              = var.cudos_dashboard.deploy_kpi_dashboard

    # Optimization Parameters
    OptimizationDataCollectionBucketPath = var.cudos_dashboard.optimization_data_collection_bucket_path
    DeployTAODashboard                   = var.cudos_dashboard.deploy_tao_dashboard
    DeployComputeOptimizerDashboard      = var.cudos_dashboard.deploy_compute_optimizer_dashboard
    PrimaryTagName                       = var.cudos_dashboard.primary_tag_name
    SecondaryTagName                     = var.cudos_dashboard.secondary_tag_name

    # Technical Parameters
    AthenaWorkgroup                  = var.cudos_dashboard.athena_workgroup
    AthenaQueryResultsBucket         = var.cudos_dashboard.athena_query_results_bucket
    DatabaseName                     = var.cudos_dashboard.database_name
    GlueDataCatalog                  = var.cudos_dashboard.glue_data_catalog
    Suffix                           = var.cudos_dashboard.suffix
    QuickSightDataSourceRoleName     = var.cudos_dashboard.quicksight_data_source_role_name
    QuickSightDataSetRefreshSchedule = var.cudos_dashboard.quicksight_data_set_refresh_schedule
    LambdaLayerBucketPrefix          = var.cudos_dashboard.lambda_layer_bucket_prefix
    DeployCUDOSDashboard             = var.cudos_dashboard.deploy_cudos_dashboard
    DataBucketsKmsKeysArns           = var.cudos_dashboard.data_buckets_kms_keys_arns
    ShareDashboard                   = var.cudos_dashboard.share_dashboard

    # Legacy Parameters
    KeepLegacyCURTable  = var.cudos_dashboard.keep_legacy_cur_table
    CURBucketPath       = var.cudos_dashboard.cur_bucket_path
    CURTableName        = var.cudos_dashboard.cur_table_name
    PermissionsBoundary = var.cudos_dashboard.permissions_boundary
    RolePath            = var.cudos_dashboard.role_path
  }
  timeouts {
    create = "60m"
    update = "60m"
    delete = "60m"
  }
}