terraform {
  required_version = ">= 1.0"
  backend "s3" {
    bucket       = "your-terraform-state-bucket"
    key          = "cid-dashboard/terraform.tfstate"
    region       = "us-east-1" # Replace with your desired region
    use_lockfile = true        # terraform-state-lock
    encrypt      = true
  }
}
