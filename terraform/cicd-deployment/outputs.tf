# Outputs for data_exports_child stack
output "data_exports_child_outputs" {
  description = "Outputs from the data exports child stack"
  value = {
    stack_id = module.data_exports_child.stack_id
    outputs  = module.data_exports_child.stack_outputs
  }
}

# Outputs for data_exports_management stack
output "data_exports_management_outputs" {
  description = "Outputs from the data exports management stack"
  value = {
    stack_id = module.data_exports_management.stack_id
    outputs  = module.data_exports_management.stack_outputs
  }
}

# Outputs for cudos_dashboard stack
output "cudos_dashboard_outputs" {
  description = "Outputs from the CUDOS dashboard stack"
  value = {
    stack_id = module.cudos_dashboard.stack_id
    outputs  = module.cudos_dashboard.stack_outputs
  }
}