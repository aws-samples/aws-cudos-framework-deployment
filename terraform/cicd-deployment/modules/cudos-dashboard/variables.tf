variable "cudos_dashboard" {
  type = object({
    # Prerequisites Variables
    prerequisites_quicksight             = string
    prerequisites_quicksight_permissions = string
    lake_formation_enabled               = string

    # CUR Parameters
    cur_version                        = string
    deploy_cudos_v5                    = string
    deploy_cost_intelligence_dashboard = string
    deploy_kpi_dashboard               = string

    # Optimization Parameters
    optimization_data_collection_bucket_path = string
    deploy_tao_dashboard                     = string
    deploy_compute_optimizer_dashboard       = string
    primary_tag_name                         = string
    secondary_tag_name                       = string

    # Technical Parameters
    athena_workgroup                     = string
    athena_query_results_bucket          = string
    database_name                        = string
    glue_data_catalog                    = string
    suffix                               = string
    quicksight_data_source_role_name     = string
    quicksight_data_set_refresh_schedule = string
    lambda_layer_bucket_prefix           = string
    deploy_cudos_dashboard               = string
    data_buckets_kms_keys_arns           = string
    share_dashboard                      = string

    # Legacy Parameters
    keep_legacy_cur_table = string
    cur_bucket_path       = string
    cur_table_name        = string
    permissions_boundary  = string
    role_path             = string
  })

  default = {
    # Prerequisites Variables
    prerequisites_quicksight             = "yes"
    prerequisites_quicksight_permissions = "yes"
    quicksight_user                      = null
    lake_formation_enabled               = "no"

    # CUR Parameters
    cur_version                        = "2.0"
    deploy_cudos_v5                    = "yes"
    deploy_cost_intelligence_dashboard = "yes"
    deploy_kpi_dashboard               = "yes"

    # Optimization Parameters
    optimization_data_collection_bucket_path = "s3://cid-data-{account_id}"
    deploy_tao_dashboard                     = "no"
    deploy_compute_optimizer_dashboard       = "no"
    primary_tag_name                         = "owner"
    secondary_tag_name                       = "environment"

    # Technical Parameters
    athena_workgroup                     = ""
    athena_query_results_bucket          = ""
    database_name                        = ""
    glue_data_catalog                    = "AwsDataCatalog"
    suffix                               = ""
    quicksight_data_source_role_name     = "CidQuickSightDataSourceRole"
    quicksight_data_set_refresh_schedule = ""
    lambda_layer_bucket_prefix           = "aws-managed-cost-intelligence-dashboards"
    deploy_cudos_dashboard               = "no"
    data_buckets_kms_keys_arns           = ""
    share_dashboard                      = "yes"

    # Legacy Parameters
    keep_legacy_cur_table = "no"
    cur_bucket_path       = "s3://cid-{account_id}-shared/cur/"
    cur_table_name        = ""
    permissions_boundary  = ""
    role_path             = "/"
  }

}

variable "global_values" {
  type = object({
    # AWS Account Id where DataExport will be replicated to
    destination_account_id = string
    # Comma separated list of source account IDs
    source_account_ids = string
    # AWS region where the dashboard will be deployed
    aws_region = string
    # Quicksight user to share the dashboard with
    quicksight_user = string
    # GitHub tag version using for the deployment (e.g. 4.0.7)
    tag_version = string
  })

  description = "Global configuration values for AWS environment"

  default = {
    destination_account_id = null
    source_account_ids     = ""
    aws_region             = ""
    quicksight_user        = null
    tag_version            = ""
  }

  validation {
    condition     = can(regex("^\\d{12}$", var.global_values.destination_account_id))
    error_message = "DestinationAccountId must be 12 digits"
  }

  validation {
    condition     = can(regex("^((\\d{12})\\,?)*$", var.global_values.source_account_ids))
    error_message = "SourceAccountIds must be comma-separated 12-digit account IDs"
  }

  validation {
    condition     = var.global_values.quicksight_user != null
    error_message = "The quicksight_user value must be provided."
  }

  validation {
    condition     = var.global_values.tag_version == "" || can(regex("^\\d+\\.\\d+\\.\\d+$", var.global_values.tag_version))
    error_message = "The tag_version must be in the format X.Y.Z where X, Y, and Z are digits (e.g., 4.0.7)"
  }
}

variable "data_exports_child_deployed" {
  description = "Manages the dependency on the data export child stack"
  type        = string
  default     = "yes"
}

variable "data_exports_management_deployed" {
  description = "Manages the dependency on the data export management stack"
  type        = string
}