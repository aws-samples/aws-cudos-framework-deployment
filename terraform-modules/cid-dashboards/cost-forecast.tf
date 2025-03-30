resource "aws_cloudformation_stack" "cost_forecast_dashboard" {
  count = contains(var.dashboards, "cost-forecast-dashboard") ? 1 : 0
  name  = "cost-forecast-dashboard-${random_string.uid.result}"

  parameters = {
    QuickSightUserName      = var.quicksight_username
    QuickSightIdentityRegion = var.quicksight_identity_region
    AthenaDatabase          = var.athena_database
    AthenaWorkGroup         = var.athena_workgroup
    CURTableName            = var.cur_table_name
    ForecastTableName       = var.forecast_table_name
    S3BucketName            = var.s3_bucket_name
    QuickSightTheme         = var.quicksight_theme
  }

  template_url = "https://aws-cudos-framework-deployment.s3.amazonaws.com/cfn-templates/cost-forecast-dashboard.yaml"

  capabilities = ["CAPABILITY_NAMED_IAM"]

  timeouts {
    create = "60m"
    update = "60m"
    delete = "60m"
  }

  tags = var.tags
}

resource "aws_lambda_permission" "cost_forecast_lambda_permission" {
  count         = contains(var.dashboards, "cost-forecast-dashboard") ? 1 : 0
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_cloudformation_stack.cost_forecast_dashboard[0].outputs["CostForecastFunction"]
  principal     = "events.amazonaws.com"
  source_arn    = "arn:aws:events:${var.region}:${data.aws_caller_identity.current.account_id}:rule/CostForecastScheduledRule-*"
}

resource "aws_s3_bucket_policy" "cost_forecast_bucket_policy" {
  count  = contains(var.dashboards, "cost-forecast-dashboard") && var.s3_bucket_name != "" ? 1 : 0
  bucket = var.s3_bucket_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "quicksight.amazonaws.com"
        }
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.s3_bucket_name}",
          "arn:aws:s3:::${var.s3_bucket_name}/*"
        ]
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = data.aws_caller_identity.current.account_id
          }
        }
      }
    ]
  })
}
