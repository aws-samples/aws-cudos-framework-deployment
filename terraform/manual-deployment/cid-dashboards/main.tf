resource "aws_cloudformation_stack" "cudos_dashboard" {
  # checkov:skip=CKV_AWS_124:SNS topic not required for this use case
  name         = "cudos-dashboard-stack"
  provider     = aws
  capabilities = ["CAPABILITY_NAMED_IAM", "CAPABILITY_IAM"]
  template_url = "https://aws-managed-cost-intelligence-dashboards.s3.amazonaws.com/cfn/${var.global_values.tag_version}/cid-cfn.yml"
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