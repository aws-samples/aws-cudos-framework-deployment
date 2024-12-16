# Outputs for data_exports_child stack
output "data_exports_child_outputs" {
  description = "Outputs from the data exports child stack"
  value = {
    stack_id = aws_cloudformation_stack.data_exports_child.id
    outputs  = aws_cloudformation_stack.data_exports_child.outputs
  }
}

# Outputs for data_exports_management stack
output "data_exports_management_outputs" {
  description = "Outputs from the data exports management stack"
  value = {
    stack_id = aws_cloudformation_stack.data_exports_management.id
    outputs  = aws_cloudformation_stack.data_exports_management.outputs
  }
}

# Outputs for cudos_dashboard stack
output "cudos_dashboard_outputs" {
  description = "Outputs from the CUDOS dashboard stack"
  value = {
    stack_id = aws_cloudformation_stack.cudos_dashboard.id
    outputs  = aws_cloudformation_stack.cudos_dashboard.outputs
  }
}

