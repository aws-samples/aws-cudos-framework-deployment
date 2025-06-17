# Outputs for data_exports_child stack
output "cid_dataexports_destination_outputs" {
  description = "Outputs from the data exports child stack"
  value = {
    stack_id = aws_cloudformation_stack.cid_dataexports_destination.id
    outputs  = aws_cloudformation_stack.cid_dataexports_destination.outputs
  }
}

# Outputs for data_exports_management stack
output "cid_dataexports_source_outputs" {
  description = "Outputs from the data exports management stack"
  value = {
    stack_id = aws_cloudformation_stack.cid_dataexports_source.id
    outputs  = aws_cloudformation_stack.cid_dataexports_source.outputs
  }
}

# Outputs for cudos_dashboard stack
output "cloud_intelligence_dashboards_outputs" {
  description = "Outputs from the CUDOS dashboard stack"
  value = {
    stack_id = aws_cloudformation_stack.cloud_intelligence_dashboards.id
    outputs  = aws_cloudformation_stack.cloud_intelligence_dashboards.outputs
  }
}
