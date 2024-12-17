# Outputs for cudos_dashboard stack
output "cudos_dashboard_outputs" {
  description = "Outputs from the CUDOS dashboard stack"
  value = {
    stack_id = aws_cloudformation_stack.cudos_dashboard.id
    outputs  = aws_cloudformation_stack.cudos_dashboard.outputs
  }
}

