module "data_exports_child" {
  source = "./modules/data-exports-child"
  providers = {
    aws = aws.destination
  }

  // Configuration
  global_values      = var.global_values
  data_exports_child = var.data_exports_child
}

module "data_exports_management" {
  source = "./modules/data-exports-management"
  providers = {
    aws = aws.management
  }

  // Configuration
  global_values           = var.global_values
  data_exports_management = var.data_exports_management

  // Makes dependency explicit
  data_exports_child_deployed = module.data_exports_child.deployed
}

module "cudos_dashboard" {
  source = "./modules/cudos-dashboard"
  providers = {
    aws = aws.destination
  }

  // Configuration
  global_values   = var.global_values
  cudos_dashboard = var.cudos_dashboard

  // Makes dependency explicit
  data_exports_child_deployed      = module.data_exports_child.deployed
  data_exports_management_deployed = module.data_exports_management.deployed
}