# Outputs for data_exports_management stack

output "stack_id" {
  description = "ID of the data exports management stack"
  value       = aws_cloudformation_stack.data_exports_management.id
}

output "stack_outputs" {
  description = "Outputs from the data exports management stack"
  value       = aws_cloudformation_stack.data_exports_management.outputs
}

output "deployed" {
  depends_on = [aws_cloudformation_stack.data_exports_management]

  description = "Manages the dependency between modules"
  value       = "yes"
}