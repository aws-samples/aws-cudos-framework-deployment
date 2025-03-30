variable "dashboards" {
  description = "List of dashboards to deploy"
  type        = list(string)
  default     = ["cudos", "cost_intelligence_dashboard", "kpi_dashboard", "trends-dashboard", "cost-forecast-dashboard"]
}

variable "quicksight_username" {
  description = "QuickSight user name"
  type        = string
  default     = ""
}

variable "quicksight_identity_region" {
  description = "QuickSight identity region"
  type        = string
  default     = "us-east-1"
}

variable "athena_database" {
  description = "Athena database name"
  type        = string
  default     = "athenacurcfn_cost_forecast"
}

variable "athena_workgroup" {
  description = "Athena workgroup name"
  type        = string
  default     = "primary"
}

variable "cur_table_name" {
  description = "CUR table name"
  type        = string
  default     = "cost_and_usage_report"
}

variable "forecast_table_name" {
  description = "Forecast data table name"
  type        = string
  default     = "cost_forecast_data"
}

variable "s3_bucket_name" {
  description = "S3 bucket name for forecast data"
  type        = string
  default     = ""
}

variable "quicksight_theme" {
  description = "QuickSight theme"
  type        = string
  default     = "MIDNIGHT"
}

variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
