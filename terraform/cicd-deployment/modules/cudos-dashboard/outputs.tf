# Outputs for cudos_dashboard stack

output "stack_id" {
  description = "ID of the CUDOS dashboard stack"
  value       = aws_cloudformation_stack.cudos_dashboard.id
}

output "stack_outputs" {
  description = "Outputs from the CUDOS dashboard stack"
  value       = aws_cloudformation_stack.cudos_dashboard.outputs
}
