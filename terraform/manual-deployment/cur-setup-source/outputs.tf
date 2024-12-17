# Outputs for data_exports_management stack
output "data_exports_management_outputs" {
  description = "Outputs from the data exports management stack"
  value = {
    stack_id = aws_cloudformation_stack.data_exports_management.id
    outputs  = aws_cloudformation_stack.data_exports_management.outputs
  }
}
