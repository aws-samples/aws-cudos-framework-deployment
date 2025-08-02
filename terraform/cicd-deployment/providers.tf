terraform {
  required_providers {
    aws = {
      source                = "hashicorp/aws"
      version               = "~> 6.0"
      configuration_aliases = [aws, aws.destination_account]
    }
  }
  required_version = ">= 1.0.0"
}
