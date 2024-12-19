variable "data_exports_child" {
  type = object({
    # Prefix used for all named resources
    resource_prefix = string
    # Enable CUR 2.0 management
    manage_cur2 = string
    # Enable FOCUS management
    manage_focus = string
    # Enable Cost Optimization Hub management
    manage_coh = string
    # Enable Split Cost Allocation Data
    enable_scad = string
    # Path for IAM roles
    role_path = string
    # Time granularity for CUR 2.0
    time_granularity = string
  })

  description = "Configuration for data exports child account settings"

  default = {
    resource_prefix  = "cid"
    manage_cur2      = "yes"
    manage_focus     = "no"
    manage_coh       = "no"
    enable_scad      = "yes"
    role_path        = "/"
    time_granularity = "HOURLY"
  }

  validation {
    condition     = can(regex("^[a-z0-9]+[a-z0-9-]{1,61}[a-z0-9]+$", var.data_exports_child.resource_prefix))
    error_message = "ResourcePrefix must match pattern ^[a-z0-9]+[a-z0-9-]{1,61}[a-z0-9]+$"
  }

  validation {
    condition     = contains(["yes", "no"], var.data_exports_child.manage_cur2)
    error_message = "ManageCUR2 must be yes or no"
  }

  validation {
    condition     = contains(["yes", "no"], var.data_exports_child.manage_focus)
    error_message = "ManageFOCUS must be yes or no"
  }

  validation {
    condition     = contains(["yes", "no"], var.data_exports_child.manage_coh)
    error_message = "ManageCOH must be yes or no"
  }

  validation {
    condition     = contains(["yes", "no"], var.data_exports_child.enable_scad)
    error_message = "EnableSCAD must be yes or no"
  }

  validation {
    condition     = contains(["HOURLY", "DAILY", "MONTHLY"], var.data_exports_child.time_granularity)
    error_message = "TimeGranularity must be HOURLY, DAILY, or MONTHLY"
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
  })

  description = "Global configuration values for AWS environment"

  default = {
    destination_account_id = null
    source_account_ids     = ""
    aws_region             = ""
  }

  validation {
    condition     = can(regex("^\\d{12}$", var.global_values.destination_account_id))
    error_message = "DestinationAccountId must be 12 digits"
  }

  validation {
    condition     = can(regex("^((\\d{12})\\,?)*$", var.global_values.source_account_ids))
    error_message = "SourceAccountIds must be comma-separated 12-digit account IDs"
  }
}
