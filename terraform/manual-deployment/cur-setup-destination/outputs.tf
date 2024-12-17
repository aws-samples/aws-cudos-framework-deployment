# Outputs for data_exports_child stack
output "data_exports_child_outputs" {
  description = "Outputs from the data exports child stack"
  value = {
    stack_id = aws_cloudformation_stack.data_exports_child.id
    outputs  = aws_cloudformation_stack.data_exports_child.outputs
  }
}