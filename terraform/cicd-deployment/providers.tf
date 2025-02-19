provider "aws" {
  region = var.global_values.aws_region
}


provider "aws" {
  alias = "destination_account"
  assume_role {
    role_arn = "arn:aws:iam::123456789012:role/<Assume_clintRole_Name>"
  }
}
