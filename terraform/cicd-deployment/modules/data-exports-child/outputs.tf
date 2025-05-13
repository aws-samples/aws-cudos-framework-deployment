# Outputs for data_exports_child stack

output "stack_id" {
  description = "ID of the data exports child stack"
  value       = aws_cloudformation_stack.data_exports_child.id
}

output "stack_outputs" {
  description = "Outputs from the data exports child stack"
  value       = aws_cloudformation_stack.data_exports_child.outputs
}

output "deployed" {
  depends_on = [aws_cloudformation_stack.data_exports_child]

  description = "Manages the dependency between modules"
  value       = "yes"
}